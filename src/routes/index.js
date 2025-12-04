const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const dashboardController = require('../controllers/dashboardController');
const configController = require('../controllers/configController');
const logController = require('../controllers/logController');
const authMiddleware = require('../middleware/auth');

router.get('/login', authController.showLoginForm);
router.post('/login', authController.login);
router.get('/logout', authController.logout);

router.get('/', authMiddleware, dashboardController.index);

router.get('/config', authMiddleware, configController.index);
router.get('/config/new', authMiddleware, configController.create);
router.post('/config', authMiddleware, configController.store);
router.get('/config/edit/:id', authMiddleware, configController.edit);
router.post('/config/update/:id', authMiddleware, configController.update);
router.get('/config/delete/:id', authMiddleware, configController.destroy);

router.get('/logs', authMiddleware, logController.index);

module.exports = router;
