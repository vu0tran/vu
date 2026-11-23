'use strict';
const { DataTypes } = require('sequelize');
module.exports = {
  up: async (queryInterface) => {
    return queryInterface.sequelize.transaction(async (t) => {
      await queryInterface.changeColumn('a', 'b', { type: DataTypes }, { transaction: t });
    });
  },
};
exports.x = 1;
