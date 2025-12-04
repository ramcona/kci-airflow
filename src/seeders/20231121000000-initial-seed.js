'use strict';
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const bcrypt = require('bcrypt');

module.exports = {
  async up (queryInterface, Sequelize) {
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash('admin123', salt);

    await queryInterface.bulkInsert('Users', [{
      email: 'admin@example.com',
      password: hashedPassword,
      createdAt: new Date(),
      updatedAt: new Date()
    }], {});

    const results = [];
    const filePath = path.join(__dirname, '../../data_table_need_to_archive.csv');

    await new Promise((resolve, reject) => {
      fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', (data) => results.push({
          database_name: data['Database'],
          schema_name: data['Schema'],
          table_name: data['Table'],
          reference_column: data['Kolom Acuan'],
          demarcation_value: data['Nilai Batas Demarkasi'],
          action_on_main: data['Aksi di Main Server'],
          action_on_archive: data['Aksi di Archive Server'],
          description: data['Keterangan'],
          is_active: true,
          createdAt: new Date(),
          updatedAt: new Date()
        }))
        .on('end', () => {
          resolve();
        })
        .on('error', (error) => {
          reject(error);
        });
    });

    await queryInterface.bulkInsert('ArchiveConfigs', results, {});
  },

  async down (queryInterface, Sequelize) {
    await queryInterface.bulkDelete('Users', null, {});
    await queryInterface.bulkDelete('ArchiveConfigs', null, {});
  }
};