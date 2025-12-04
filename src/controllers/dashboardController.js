const { ArchiveConfig, ActivityLog } = require('../models');

exports.index = async (req, res) => {
  try {
    const totalConfigs = await ArchiveConfig.count();
    const lastAirflowLog = await ActivityLog.findOne({
      where: { source: 'AIRFLOW_DAG' },
      order: [['createdAt', 'DESC']]
    });

    res.render('dashboard', {
      title: 'Dashboard',
      totalConfigs,
      lastAirflowLog
    });
  } catch (error) {
    console.error(error);
    res.status(500).send("Terjadi kesalahan saat memuat dashboard.");
  }
};
