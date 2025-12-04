'use strict';

/** @type {import('sequelize-cli').Migration} */
module.exports = {
  async up (queryInterface, Sequelize) {
    await queryInterface.addColumn('ArchiveConfigs', 'demarcation_value_temp', {
      type: Sequelize.INTEGER,
      allowNull: true,
    });

    await queryInterface.removeColumn('ArchiveConfigs', 'demarcation_value');

    await queryInterface.renameColumn('ArchiveConfigs', 'demarcation_value_temp', 'demarcation_value');
  },

  async down (queryInterface, Sequelize) {
    await queryInterface.addColumn('ArchiveConfigs', 'demarcation_value_temp', {
      type: Sequelize.STRING,
      allowNull: true,
    });

    await queryInterface.sequelize.query('UPDATE "ArchiveConfigs" SET "demarcation_value_temp" = CAST("demarcation_value" AS TEXT) WHERE "demarcation_value" IS NOT NULL;');

    await queryInterface.removeColumn('ArchiveConfigs', 'demarcation_value');

    await queryInterface.renameColumn('ArchiveConfigs', 'demarcation_value_temp', 'demarcation_value');
  }
};
