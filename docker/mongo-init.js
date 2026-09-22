db = db.getSiblingDB('earthquakes');
db.earthquakes.createIndex({ event_id: 1 }, { unique: true });
db.earthquakes.createIndex({ event_time: -1 });
db.earthquakes.createIndex({ magnitude: -1 });
db.metrics.createIndex({ window: 1 }, { unique: true });
db.hourly_reports.createIndex({ report_date: 1 }, { unique: true });
