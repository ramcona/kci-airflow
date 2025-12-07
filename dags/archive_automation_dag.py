import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.models.baseoperator import chain
from airflow.models import Variable
import json

from datetime import timedelta

log = LoggingMixin().log

# Konfigurasi koneksi database
APP_DB_CONN_ID = "postgres_app"
MAIN_DB_CONN_ID = "postgres_main"
ARCHIVE_DB_CONN_ID = "postgres_archive"

# Define default_args for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['rafliramadhanco@gmail.com'],
    'email_on_failure': True,
    'email_on_success': True,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

def _get_active_archive_configs(**kwargs):
    """
    Membaca konfigurasi arsip yang aktif dari database aplikasi.
    Menggunakan XCom untuk menyimpan konfigurasi agar dapat diakses oleh task selanjutnya.
    """
    try:
        log.info(f"Mencoba koneksi ke database dengan conn_id: {APP_DB_CONN_ID}")
        app_hook = PostgresHook(postgres_conn_id=APP_DB_CONN_ID)
        
        # Test connection first
        conn = app_hook.get_conn()
        log.info("Koneksi database berhasil!")
        
        # AUTO-DETECT: Get all columns from the table
        log.info("Mendeteksi kolom yang tersedia di tabel ArchiveConfigs...")
        column_check_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ArchiveConfigs'
            ORDER BY ordinal_position;
        """
        available_columns = [row[0] for row in app_hook.get_records(column_check_sql)]
        log.info(f"Kolom yang tersedia: {available_columns}")
        
        # Build SQL query dynamically based on available columns
        columns_to_select = []
        column_names = []
        
        # Required columns (must exist)
        required_cols = ['id', 'database_name', 'schema_name', 'table_name', 'reference_column', 'demarcation_value', 
                        'action_on_main', 'action_on_archive', 'description', 'is_active']
        
        optional_cols = [
            ('createdAt', 'created_at'),
            ('updatedAt', 'updated_at')
        ]
        
        # Add required columns
        for col in required_cols:
            if col in available_columns:
                columns_to_select.append(f'"{col}"')
                column_names.append(col)
            else:
                log.warning(f"Kolom wajib '{col}' tidak ditemukan!")
        
        for camel, snake in optional_cols:
            if camel in available_columns:
                columns_to_select.append(f'"{camel}"')
                column_names.append(camel)
            elif snake in available_columns:
                columns_to_select.append(f'"{snake}"')
                column_names.append(snake)
        
        sql = f"SELECT {', '.join(columns_to_select)} FROM \"ArchiveConfigs\" WHERE is_active = TRUE;"
        
        log.info(f"Menjalankan query: {sql}")
        configs = app_hook.get_records(sql)
        log.info(f"Query berhasil, mendapat {len(configs) if configs else 0} records")
        
        if not configs:
            log.warning("Tidak ada konfigurasi aktif ditemukan!")
            return []
        
        configs_dicts = []
        for idx, config_tuple in enumerate(configs):
            log.info(f"Processing config {idx + 1}/{len(configs)}")
            # Convert datetime objects to strings for JSON serialization
            config_dict = {}
            for i, key in enumerate(column_names):
                value = config_tuple[i]
                if hasattr(value, 'isoformat'):
                    config_dict[key] = value.isoformat()
                elif isinstance(value, (list, dict)):
                    config_dict[key] = json.dumps(value)
                else:
                    config_dict[key] = value
            configs_dicts.append(config_dict)
            log.info(f"Config {idx + 1}: {config_dict.get('schema_name')}.{config_dict.get('table_name')}")

        log.info(f"Ditemukan {len(configs_dicts)} konfigurasi aktif.")
        log.info(f"Sample config: {configs_dicts[0] if configs_dicts else 'None'}")
        
        return configs_dicts
        
    except Exception as e:
        log.error(f"ERROR di _get_active_archive_configs: {type(e).__name__}")
        log.error(f"Error message: {str(e)}")
        log.error(f"Full traceback:", exc_info=True)
        raise

def _check_db_connections():
    """
    Melakukan pengecekan koneksi ke semua database yang diperlukan.
    """
    log.info("Memulai pengecekan koneksi database...")
    
    # Check APP_DB_CONN_ID
    try:
        app_hook = PostgresHook(postgres_conn_id=APP_DB_CONN_ID)
        app_hook.get_conn()
        log.info(f"Koneksi ke database aplikasi ({APP_DB_CONN_ID}) berhasil.")
    except Exception as e:
        log.error(f"Gagal terhubung ke database aplikasi ({APP_DB_CONN_ID}): {e}")
        raise

    # Check MAIN_DB_CONN_ID
    try:
        main_hook = PostgresHook(postgres_conn_id=MAIN_DB_CONN_ID)
        main_hook.get_conn()
        log.info(f"Koneksi ke database utama ({MAIN_DB_CONN_ID}) berhasil.")
    except Exception as e:
        log.error(f"Gagal terhubung ke database utama ({MAIN_DB_CONN_ID}): {e}")
        raise

    # Check ARCHIVE_DB_CONN_ID
    try:
        archive_hook = PostgresHook(postgres_conn_id=ARCHIVE_DB_CONN_ID)
        archive_hook.get_conn()
        log.info(f"Koneksi ke database arsip ({ARCHIVE_DB_CONN_ID}) berhasil.")
    except Exception as e:
        log.error(f"Gagal terhubung ke database arsip ({ARCHIVE_DB_CONN_ID}): {e}")
        raise
    
    log.info("Semua koneksi database berhasil.")

def _parse_condition(ref_col, demarc_val):
    """
    Menganalisis deskripsi untuk membangun kondisi SQL yang dinamis.
    Menggunakan demarc_val sebagai jumlah hari.
    """
    # Ensure demarc_val is treated as an integer
    try:
        demarc_days = int(demarc_val)
    except (ValueError, TypeError):
        log.error(f"Invalid demarcation_value: {demarc_val}. Expected an integer representing days.")
        raise ValueError("demarcation_value must be an integer representing days.")

    # Construct the condition to archive data older than demarc_days
    condition = f"{ref_col} < NOW() - INTERVAL '{demarc_days} days'"
    return condition

def _log_activity(app_hook, level, source, message, log_prefix=""):
    """Mencatat aktivitas ke tabel ActivityLogs dengan parameterized query."""
    full_message = f"{log_prefix} {message}".strip()
    sql = """
        INSERT INTO "ActivityLogs" (level, source, message, "createdAt", "updatedAt") 
        VALUES (%s, %s, %s, NOW(), NOW());
    """
    try:
        app_hook.run(sql, parameters=(level, source, full_message))
    except Exception as e:
        log.error(f"Failed to log activity: {e}")

def _ensure_schema_and_table_exists(single_config: dict, **kwargs):
    """
    Ensures the archive schema and table exist and synchronizes the table structure
    with the source table.
    """
    schema_name = single_config['schema_name']
    table_name = single_config['table_name']
    log_prefix = f"[{schema_name}.{table_name}]"
    log.info(f"{log_prefix} Starting schema and table synchronization.")

    main_hook = PostgresHook(postgres_conn_id=MAIN_DB_CONN_ID)
    archive_hook = PostgresHook(postgres_conn_id=ARCHIVE_DB_CONN_ID)
    app_hook = PostgresHook(postgres_conn_id=APP_DB_CONN_ID)

    def get_table_schema(hook, schema, table):
        sql = """
            SELECT column_name, data_type, udt_name, character_maximum_length, 
                   numeric_precision, numeric_scale, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """
        records = hook.get_records(sql, parameters=(schema, table))
        if not records:
            return {}
        return {row[0]: {
            "data_type": row[1],
            "udt_name": row[2],
            "char_max_len": row[3],
            "num_prec": row[4],
            "num_scale": row[5],
            "is_nullable": row[6]
        } for row in records}

    def get_column_definition(col_name, col_attrs):
        """Generates a SQL column definition string."""
        data_type = col_attrs['data_type']
        udt_name = col_attrs['udt_name']
        
        type_str = udt_name if data_type == 'USER-DEFINED' else data_type

        if type_str in ('character varying', 'varchar') and col_attrs['char_max_len']:
            type_str += f"({col_attrs['char_max_len']})"
        elif type_str == 'numeric' and col_attrs['num_prec'] and col_attrs['num_scale'] is not None:
            type_str += f"({col_attrs['num_prec']}, {col_attrs['num_scale']})"
        elif type_str == 'numeric' and col_attrs['num_prec']:
            type_str += f"({col_attrs['num_prec']})"
        
        definition = f'"{col_name}" {type_str}'
        if col_attrs['is_nullable'] == 'NO':
            definition += ' NOT NULL'
        return definition

    try:
        if not schema_name.replace('_', '').isalnum() or not table_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid schema or table name: {schema_name}.{table_name}")

        archive_hook.run(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
        log.info(f"{log_prefix} Schema '{schema_name}' is present.")

        table_exists = archive_hook.get_first(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = %s AND tablename = %s);",
            parameters=(schema_name, table_name)
        )[0]

        source_schema = get_table_schema(main_hook, schema_name, table_name)
        if not source_schema:
            raise ValueError(f"Source table '{schema_name}.{table_name}' not found in main database.")

        if not table_exists:
            log.warning(f"{log_prefix} Table does not exist in archive. Creating it...")
            column_defs = [get_column_definition(name, attrs) for name, attrs in source_schema.items()]
            create_sql = f"CREATE TABLE {schema_name}.{table_name} ({', '.join(column_defs)});"
            archive_hook.run(create_sql)
            log.info(f"{log_prefix} Table created successfully.")
            _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', "Table created in archive.", log_prefix)
            return

        log.info(f"{log_prefix} Table exists. Comparing schema with source...")
        archive_schema = get_table_schema(archive_hook, schema_name, table_name)
        
        source_cols = set(source_schema.keys())
        archive_cols = set(archive_schema.keys())

        alter_statements = []

        cols_to_add = source_cols - archive_cols
        for col_name in cols_to_add:
            col_def = get_column_definition(col_name, source_schema[col_name])
            alter_statements.append(f'ADD COLUMN {col_def}')
            log.info(f"{log_prefix} Will add column: {col_name}")

        cols_to_drop = archive_cols - source_cols
        for col_name in cols_to_drop:
            alter_statements.append(f'DROP COLUMN "{col_name}"')
            log.warning(f"{log_prefix} Will drop column: {col_name}")

        for col_name in source_cols.intersection(archive_cols):
            source_col = source_schema[col_name]
            archive_col = archive_schema[col_name]
            
            source_type_str = get_column_definition(col_name, source_col).split('" ')[1].split(' NOT')[0]
            archive_type_str = get_column_definition(col_name, archive_col).split('" ')[1].split(' NOT')[0]

            if source_type_str != archive_type_str:
                alter_statements.append(f'ALTER COLUMN "{col_name}" TYPE {source_type_str} USING "{col_name}"::{source_type_str}')
                log.info(f"{log_prefix} Will modify column type for: {col_name} from '{archive_type_str}' to '{source_type_str}'")

            if source_col['is_nullable'] != archive_col['is_nullable']:
                if source_col['is_nullable'] == 'NO':
                    alter_statements.append(f'ALTER COLUMN "{col_name}" SET NOT NULL')
                    log.info(f"{log_prefix} Will set NOT NULL for column: {col_name}")
                else:
                    alter_statements.append(f'ALTER COLUMN "{col_name}" DROP NOT NULL')
                    log.info(f"{log_prefix} Will drop NOT NULL for column: {col_name}")

        if not alter_statements:
            log.info(f"{log_prefix} Schema is already in sync.")
            _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', "Schema already in sync.", log_prefix)
        else:
            log.info(f"{log_prefix} Applying {len(alter_statements)} schema changes...")
            full_alter_sql = f"ALTER TABLE {schema_name}.{table_name} {', '.join(alter_statements)};"
            archive_hook.run(full_alter_sql)
            log.info(f"{log_prefix} Schema synchronization successful.")
            _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', f"Applied {len(alter_statements)} schema changes.", log_prefix)

    except Exception as e:
        error_msg = f"Error during schema synchronization: {e}"
        log.error(f"{log_prefix} {error_msg}", exc_info=True)
        _log_activity(app_hook, 'ERROR', 'AIRFLOW_DAG', error_msg, log_prefix)
        raise

def _transfer_data_to_archive(single_config: dict, **kwargs):
    """
    Memindahkan data dari DB Main ke DB Archive berdasarkan konfigurasi.
    """
    schema_name = single_config['schema_name']
    table_name = single_config['table_name']
    ref_col = single_config['reference_column']
    demarc_val = single_config['demarcation_value']
    description = single_config['description']

    log_prefix = f"[{schema_name}.{table_name}]"
    log.info(f"{log_prefix} Memulai transfer data ke arsip.")

    main_hook = PostgresHook(postgres_conn_id=MAIN_DB_CONN_ID)
    archive_hook = PostgresHook(postgres_conn_id=ARCHIVE_DB_CONN_ID)
    app_hook = PostgresHook(postgres_conn_id=APP_DB_CONN_ID)

    try:
        condition = _parse_condition(ref_col, demarc_val)
        select_sql = f"SELECT * FROM {schema_name}.{table_name} WHERE {condition};"
        
        data_to_archive = main_hook.get_records(select_sql)
        
        if not data_to_archive:
            log.info(f"{log_prefix} Tidak ada data untuk diarsipkan. Melewati transfer.")
            _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', "Tidak ada data untuk diarsipkan.", log_prefix)
            # Return values to be used by downstream tasks
            return {
                'rows_archived': 0,
                'archive_condition': condition,
                'validation_success': True,
                'config': single_config
            }

        log.info(f"{log_prefix} Ditemukan {len(data_to_archive)} baris untuk diarsipkan.")

        # Get target fields from information_schema.columns for the source table
        get_columns_sql = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
            ORDER BY ordinal_position;
        """
        target_fields = [row[0] for row in main_hook.get_records(get_columns_sql)]

        archive_hook.insert_rows(table=f"{schema_name}.{table_name}", rows=data_to_archive, target_fields=target_fields)
        
        log.info(f"{log_prefix} {len(data_to_archive)} baris berhasil ditransfer ke arsip.")
        _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', f"{len(data_to_archive)} baris berhasil ditransfer ke arsip.", log_prefix)
        
        # Return all necessary data for downstream tasks
        return {
            'rows_archived': len(data_to_archive),
            'archive_condition': condition,
            'config': single_config
        }
    except Exception as e:
        error_msg = f"Terjadi error saat transfer data: {e}"
        log.error(f"{log_prefix} {error_msg}")
        _log_activity(app_hook, 'ERROR', 'AIRFLOW_DAG', error_msg, log_prefix)
        raise

def _validate_archived_data(transfer_result: dict, **kwargs):
    """
    Melakukan validasi data yang diarsipkan dengan membandingkan jumlah baris.
    """
    single_config = transfer_result['config']
    rows_archived = transfer_result['rows_archived']
    archive_condition = transfer_result['archive_condition']
    
    schema_name = single_config['schema_name']
    table_name = single_config['table_name']
    
    log_prefix = f"[{schema_name}.{table_name}]"
    log.info(f"{log_prefix} Memulai validasi data arsip.")

    archive_hook = PostgresHook(postgres_conn_id=ARCHIVE_DB_CONN_ID)
    app_hook = PostgresHook(postgres_conn_id=APP_DB_CONN_ID)

    if rows_archived == 0:
        log.info(f"{log_prefix} Tidak ada baris yang diarsipkan, validasi dilewati.")
        _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', "Validasi dilewati: tidak ada baris yang diarsipkan.", log_prefix)
        return {
            'validation_success': True,
            'rows_archived': rows_archived,
            'archive_condition': archive_condition,
            'config': single_config
        }

    try:
        count_archived_sql = f"SELECT COUNT(*) FROM {schema_name}.{table_name} WHERE {archive_condition};"
        rows_in_archive_db = archive_hook.get_first(count_archived_sql)[0]

        if rows_in_archive_db >= rows_archived:  # >= to handle concurrent inserts
            log.info(f"{log_prefix} Validasi sukses: {rows_archived} baris cocok di arsip (found {rows_in_archive_db}).")
            _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', f"Validasi sukses: {rows_archived} baris cocok.", log_prefix)
            return {
                'validation_success': True,
                'rows_archived': rows_archived,
                'archive_condition': archive_condition,
                'config': single_config
            }
        else:
            error_msg = f"Validasi Gagal: Jumlah baris tidak cocok (Ditransfer: {rows_archived}, Ditemukan di Arsip: {rows_in_archive_db})."
            log.error(f"{log_prefix} {error_msg}")
            _log_activity(app_hook, 'ERROR', 'AIRFLOW_DAG', error_msg, log_prefix)
            raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Terjadi error saat validasi data: {e}"
        log.error(f"{log_prefix} {error_msg}")
        _log_activity(app_hook, 'ERROR', 'AIRFLOW_DAG', error_msg, log_prefix)
        raise

def _purge_data_from_main(validation_result: dict, **kwargs):
    """
    Menghapus data dari DB Main jika validasi sukses dan dikonfigurasi.
    """
    single_config = validation_result['config']
    validation_success = validation_result['validation_success']
    archive_condition = validation_result['archive_condition']
    rows_archived = validation_result['rows_archived']
    
    schema_name = single_config['schema_name']
    table_name = single_config['table_name']
    action_main = single_config['action_on_main']

    log_prefix = f"[{schema_name}.{table_name}]"
    log.info(f"{log_prefix} Memulai proses penghapusan data dari utama.")

    main_hook = PostgresHook(postgres_conn_id=MAIN_DB_CONN_ID)
    app_hook = PostgresHook(postgres_conn_id=APP_DB_CONN_ID)

    if not validation_success:
        log.warning(f"{log_prefix} Validasi gagal, penghapusan data dibatalkan.")
        _log_activity(app_hook, 'WARNING', 'AIRFLOW_DAG', "Penghapusan data dibatalkan karena validasi gagal.", log_prefix)
        return {
            'purge_success': False,
            'config': single_config,
            'validation_success': validation_success,
            'rows_archived': rows_archived
        }

    if rows_archived == 0:
        log.info(f"{log_prefix} Tidak ada baris yang diarsipkan, penghapusan dilewati.")
        _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', "Penghapusan dilewati: tidak ada baris yang diarsipkan.", log_prefix)
        return {
            'purge_success': True,
            'config': single_config,
            'validation_success': validation_success,
            'rows_archived': rows_archived
        }

    if action_main.lower() == 'hapus setelah clone':
        try:
            delete_sql = f"DELETE FROM {schema_name}.{table_name} WHERE {archive_condition};"
            main_hook.run(delete_sql)
            log.info(f"{log_prefix} Data lama berhasil dihapus dari server utama.")
            _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', f"{rows_archived} baris berhasil dihapus dari sumber.", log_prefix)
            return {
                'purge_success': True,
                'config': single_config,
                'validation_success': validation_success,
                'rows_archived': rows_archived
            }
        except Exception as e:
            error_msg = f"Terjadi error saat menghapus data dari utama: {e}"
            log.error(f"{log_prefix} {error_msg}")
            _log_activity(app_hook, 'ERROR', 'AIRFLOW_DAG', error_msg, log_prefix)
            raise
    else:
        log.info(f"{log_prefix} Aksi '{action_main}' tidak memerlukan penghapusan.")
        _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', f"Aksi '{action_main}' tidak memerlukan penghapusan.", log_prefix)
        return {
            'purge_success': True,
            'config': single_config,
            'validation_success': validation_success,
            'rows_archived': rows_archived
        }

def _log_final_status(purge_result: dict, **kwargs):
    """
    Mencatat status akhir proses pengarsipan untuk konfigurasi ini.
    """
    single_config = purge_result['config']
    validation_success = purge_result['validation_success']
    rows_archived = purge_result['rows_archived']
    
    schema_name = single_config['schema_name']
    table_name = single_config['table_name']
    
    log_prefix = f"[{schema_name}.{table_name}]"
    log.info(f"{log_prefix} Mencatat status akhir.")

    app_hook = PostgresHook(postgres_conn_id=APP_DB_CONN_ID)
    
    try:
        if validation_success is True and rows_archived > 0:
            message = f"Proses pengarsipan untuk {schema_name}.{table_name} berhasil. {rows_archived} baris diarsipkan."
            _log_activity(app_hook, 'SUCCESS', 'AIRFLOW_DAG', message, log_prefix)
            log.info(f"{log_prefix} {message}")
        elif validation_success is False:
            message = f"Proses pengarsipan untuk {schema_name}.{table_name} gagal karena validasi data."
            _log_activity(app_hook, 'FAILED', 'AIRFLOW_DAG', message, log_prefix)
            log.error(f"{log_prefix} {message}")
        else:
            message = f"Proses pengarsipan untuk {schema_name}.{table_name} selesai tanpa data diarsipkan."
            _log_activity(app_hook, 'INFO', 'AIRFLOW_DAG', message, log_prefix)
            log.info(f"{log_prefix} {message}")

    except Exception as e:
        error_msg = f"Terjadi error saat mencatat status akhir: {e}"
        log.error(f"{log_prefix} {error_msg}")
        _log_activity(app_hook, 'ERROR', 'AIRFLOW_DAG', error_msg, log_prefix)
        raise


with DAG(
    dag_id="archive_automation_dag",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    schedule_interval=Variable.get("archive_automation_schedule_interval", default_var="@daily"),
    catchup=False,
    tags=["archive", "postgres"],
    default_args=default_args,
    doc_md="""
    ### DAG Otomasi Pengarsipan Data
    DAG ini bertanggung jawab untuk mengotomatisasi proses pengarsipan data
    dari database utama ke database arsip berdasarkan konfigurasi yang aktif.
    """
) as dag:
    check_db_connections_task = PythonOperator(
        task_id="check_db_connections",
        python_callable=_check_db_connections,
    )

    get_configs_task = PythonOperator(
        task_id="get_active_configs",
        python_callable=_get_active_archive_configs,
    )

    ensure_schema_task = PythonOperator.partial(
        task_id="ensure_schema_and_table_exists",
        python_callable=_ensure_schema_and_table_exists,
    ).expand(
        op_kwargs=get_configs_task.output.map(lambda config: {"single_config": config})
    )

    transfer_data_task = PythonOperator.partial(
        task_id="transfer_data_to_archive",
        python_callable=_transfer_data_to_archive,
    ).expand(
        op_kwargs=get_configs_task.output.map(lambda config: {"single_config": config})
    )

    validate_data_task = PythonOperator.partial(
        task_id="validate_archived_data",
        python_callable=_validate_archived_data,
    ).expand(
        op_kwargs=transfer_data_task.output.map(lambda result: {"transfer_result": result})
    )

    purge_data_task = PythonOperator.partial(
        task_id="purge_data_from_main",
        python_callable=_purge_data_from_main,
    ).expand(
        op_kwargs=validate_data_task.output.map(lambda result: {"validation_result": result})
    )

    log_status_task = PythonOperator.partial(
        task_id="log_final_status",
        python_callable=_log_final_status,
    ).expand(
        op_kwargs=purge_data_task.output.map(lambda result: {"purge_result": result})
    )

    # Define task dependencies
    check_db_connections_task >> get_configs_task
    get_configs_task >> ensure_schema_task >> transfer_data_task >> validate_data_task >> purge_data_task >> log_status_task