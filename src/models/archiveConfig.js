'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class ArchiveConfig extends Model {
    static associate(models) {
    }
  }
  ArchiveConfig.init({
    database_name: DataTypes.STRING,
    schema_name: DataTypes.STRING,
    table_name: DataTypes.STRING,
    reference_column: DataTypes.STRING,
    demarcation_value: DataTypes.INTEGER,
    action_on_main: DataTypes.STRING,
    action_on_archive: DataTypes.STRING,
    description: DataTypes.TEXT,
    is_active: {
      type: DataTypes.BOOLEAN,
      defaultValue: true
    }
  }, {
    sequelize,
    modelName: 'ArchiveConfig',
  });
  return ArchiveConfig;
};