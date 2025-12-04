require('dotenv').config();
const express = require('express');
const session = require('express-session');
const path = require('path');
const expressLayouts = require('express-ejs-layouts');
const routes = require('./routes');

const app = express();
const port = process.env.APP_PORT || 3000;

app.use(expressLayouts);
app.set('layout', './layouts/main');
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, '../../public'))); 

app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: true,
  cookie: { secure: false } 
}));

app.use((req, res, next) => {
  res.locals.session = req.session;
  next();
});

app.use('/', routes);

app.listen(port, () => {
  console.log(`Aplikasi berjalan di http://localhost:${port}`);
});

module.exports = app;
