const { User } = require('../models');

exports.index = async (req, res) => {
  const users = await User.findAll();
  res.render('users/index', { users, layout: 'layouts/main', title: 'User Management' });
};

exports.create = (req, res) => {
  res.render('users/create', { layout: 'layouts/main', title: 'Create User' });
};

exports.store = async (req, res) => {
  try {
    const { name, email, password, role } = req.body;
    await User.create({ name, email, password, role });
    res.redirect('/users');
  } catch (error) {
    res.render('users/create', { error, layout: 'layouts/main', title: 'Create User' });
  }
};

exports.edit = async (req, res) => {
  const user = await User.findByPk(req.params.id);
  res.render('users/edit', { user, layout: 'layouts/main', title: 'Edit User' });
};

exports.update = async (req, res) => {
  try {
    const user = await User.findByPk(req.params.id);
    const { name, email, password, role } = req.body;
    await user.update({ name, email, password, role });
    res.redirect('/users');
  } catch (error) {
    const user = await User.findByPk(req.params.id);
    res.render('users/edit', { user, error, layout: 'layouts/main', title: 'Edit User' });
  }
};

exports.destroy = async (req, res) => {
  const user = await User.findByPk(req.params.id);
  await user.destroy();
  res.redirect('/users');
};
