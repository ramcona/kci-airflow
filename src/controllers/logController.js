const { ActivityLog } = require('../models');

exports.index = async (req, res) => {
  try {
    const logs = await ActivityLog.findAll({
      order: [['createdAt', 'DESC']],
      limit: 100 
    });
    res.render('logs', {
      title: 'Activity Logs',
      logs
    });
  } catch (error)
  {
    console.error(error);
    res.status(500).send("Terjadi kesalahan saat memuat logs.");
  }
};
