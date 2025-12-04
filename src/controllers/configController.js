const { ArchiveConfig, ActivityLog } = require('../models');

exports.index = async (req, res) => {
  try {
    const configs = await ArchiveConfig.findAll({ order: [['createdAt', 'DESC']] });
    res.render('config/index', { title: 'Manajemen Konfigurasi', configs });
  } catch (error) {
    console.error(error);
    res.status(500).send("Error memuat halaman konfigurasi.");
  }
};

exports.create = (req, res) => {
  res.render('config/create', { title: 'Tambah Konfigurasi Baru' });
};

exports.store = async (req, res) => {
  try {
    const { demarcation_value, ...otherBody } = req.body;
    const newConfig = {
      ...otherBody,
      demarcation_value: parseInt(demarcation_value, 10),
    };
    await ArchiveConfig.create(newConfig);
    await ActivityLog.create({
      level: 'INFO',
      source: 'WEB_APP',
      message: `Konfigurasi baru ditambahkan: ${req.body.table_name}`,
      user_email: req.session.userEmail
    });
    res.redirect('/config');
  } catch (error) {
    console.error(error);
    res.status(500).send("Error menyimpan konfigurasi.");
  }
};

exports.edit = async (req, res) => {
  try {
    const config = await ArchiveConfig.findByPk(req.params.id);
    res.render('config/edit', { title: 'Edit Konfigurasi', config });
  } catch (error) {
    console.error(error);
    res.status(500).send("Error memuat halaman edit.");
  }
};

exports.update = async (req, res) => {
  try {
    const { demarcation_value, ...otherBody } = req.body;
    const updatedConfig = {
      ...otherBody,
      demarcation_value: parseInt(demarcation_value, 10),
    };
    await ArchiveConfig.update(updatedConfig, { where: { id: req.params.id } });
    await ActivityLog.create({
      level: 'INFO',
      source: 'WEB_APP',
      message: `Konfigurasi diperbarui: ${req.body.table_name}`,
      user_email: req.session.userEmail
    });
    res.redirect('/config');
  } catch (error) {
    console.error(error);
    res.status(500).send("Error mengupdate konfigurasi.");
  }
};

exports.destroy = async (req, res) => {
  try {
    const config = await ArchiveConfig.findByPk(req.params.id);
    await config.destroy();
    await ActivityLog.create({
      level: 'WARNING',
      source: 'WEB_APP',
      message: `Konfigurasi dihapus: ${config.table_name}`,
      user_email: req.session.userEmail
    });
    res.redirect('/config');
  } catch (error) {
    console.error(error);
    res.status(500).send("Error menghapus konfigurasi.");
  }
};
