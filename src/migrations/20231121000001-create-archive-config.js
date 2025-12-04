'use strict';
/** @type {import('sequelize-cli').Migration} */
module.exports = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('ArchiveConfigs', {
      id: {
        allowNull: false,
        autoIncrement: true,
        primaryKey: true,
        type: Sequelize.INTEGER
      },
      database_name: {
        type: Sequelize.STRING
      },
      schema_name: {
        type: Sequelize.STRING
      },
      table_name: {
        type: Sequelize.STRING
      },
      reference_column: {
        type: Sequelize.STRING
      },
      demarcation_value: {
        type: Sequelize.STRING
      },
      action_on_main: {
        type: Sequelize.STRING
      },
      action_on_archive: {
        type: Sequelize.STRING
      },
      description: {
        type: Sequelize.TEXT
      },
      is_active: {
        type: Sequelize.BOOLEAN,
        defaultValue: true
      },
      createdAt: {
        allowNull: false,
        type: Sequelize.DATE
      },
      updatedAt: {
        allowNull: false,
        type: Sequelize.DATE
      }
    });
  },
  async down(queryInterface, Sequelize) {
    await queryInterface.dropTable('ArchiveConfigs');
  }
};