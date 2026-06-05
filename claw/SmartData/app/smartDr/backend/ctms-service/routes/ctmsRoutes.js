const express = require('express');
const router = express.Router();
const {
  getTrials,
  createTrial,
  getTrialDetails,
  updateTrial,
  deleteTrial,
  getStudySites,
  createStudySite,
  getTimeEntries,
  createTimeEntry,
  updateTimeEntry,
  deleteTimeEntry,
  getTimeEntryReport
} = require('../controllers/ctmsController');

// 试验管理相关路由
router.get('/trials', getTrials);
router.post('/trials', createTrial);
router.get('/trials/:id', getTrialDetails);
router.put('/trials/:id', updateTrial);
router.delete('/trials/:id', deleteTrial);

// 研究中心相关路由
router.get('/study-sites', getStudySites);
router.post('/study-sites', createStudySite);

// 工时管理相关路由
router.get('/time-entries', getTimeEntries);
router.post('/time-entries', createTimeEntry);
router.put('/time-entries/:id', updateTimeEntry);
router.delete('/time-entries/:id', deleteTimeEntry);
router.get('/time-report', getTimeEntryReport);

module.exports = router;