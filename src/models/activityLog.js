'use strict';
const {
  Model
} = require('sequelize');
module.exports = (sequelize, DataTypes) => {
  class ActivityLog extends Model {
    static associate(models) {
    }
  }
  ActivityLog.init({
    level: DataTypes.STRING, // INFO, WARNING, ERROR
    source: DataTypes.STRING, // WEB_APP, AIRFLOW_DAG
    message: DataTypes.TEXT,
    details: DataTypes.JSONB,
    user_email: DataTypes.STRING 
  }, {
    sequelize,
    modelName: 'ActivityLog',
  });
  return ActivityLog;
};