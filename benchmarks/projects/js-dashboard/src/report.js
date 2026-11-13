const {total} = require('./metrics');
function summarize(points) { return {sum: total(points),count: points.length}; }
module.exports={summarize};
