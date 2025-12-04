const { User } = require('../models');
const bcrypt = require('bcrypt');

exports.showLoginForm = (req, res) => {
  res.render('login', { 
    title: 'Login Admin', 
    layout: './layouts/login', 
    error: null 
  });
};

exports.login = async (req, res) => {
  const { email, password } = req.body;
  try {
    const user = await User.findOne({ where: { email } });

    if (user && await user.validPassword(password)) {
      req.session.userId = user.id;
      req.session.userEmail = user.email;
      res.redirect('/');
    } else {
      res.render('login', { 
        title: 'Login Admin', 
        layout: './layouts/login',
        error: 'Email atau password salah.' 
      });
    }
  } catch (error) {
    console.error(error);
    res.render('login', { 
      title: 'Login Admin', 
      layout: './layouts/login',
      error: 'Terjadi kesalahan pada server.' 
    });
  }
};

// Proses logout
exports.logout = (req, res) => {
  req.session.destroy(err => {
    if (err) {
      return res.redirect('/');
    }
    res.clearCookie('connect.sid');
    res.redirect('/login');
  });
};
