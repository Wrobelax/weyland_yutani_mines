function onEdit(e) {
  const sheet = e.source.getSheetByName("Config");
  if (!sheet) return;

  const edited = e.range.getA1Notation();

  if (e.range.getRow() >= 3 && e.range.getRow() <= 16) {
    regenData();
  }
}

function regenData() {
  const ss = SpreadsheetApp.getActive();
  const cfg = ss.getSheetByName("Config");
  if (!cfg) {
    SpreadsheetApp.getUi().alert("Sheet 'Config' not found.");
    return;
  }

  // ---------------------
  // HELPERS
  // ---------------------
  function toNum(x) {
    if (x === "" || x === null || x === undefined) return 0;
    if (typeof x === "number") return x;
    const s = String(x).replace(",", ".").trim();
    return s === "" ? 0 : Number(s);
  }
  function toDate(x) {
    if (!x && x !== 0) return null;
    if (x instanceof Date) return new Date(x.getFullYear(), x.getMonth(), x.getDate());
    const d = new Date(x);
    if (isNaN(d.getTime())) return null;
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  // ---------------------
  // CORE SETTINGS
  // ---------------------
  const startDate = toDate(cfg.getRange("B3").getValue());
  const daysCount = Math.max(0, Math.floor(toNum(cfg.getRange("B4").getValue())));

  if (!startDate || daysCount <= 0) {
    SpreadsheetApp.getUi().alert("Invalid start date or days count (B3 & B4)");
    return;
  }

  // ---------------------
  // MINES  (B5:H5)
  // ---------------------
  const mines = cfg
    .getRange("B5:H5")
    .getValues()[0]
    .map(v => (v === null ? "" : String(v).trim()))
    .filter(v => v !== "");

  const mineCount = mines.length;
  if (mineCount === 0) {
    SpreadsheetApp.getUi().alert("No mine names defined in row 5.");
    return;
  }

  // ---------------------
  // DISTRIBUTION SETTINGS
  // ---------------------
  const distribution = String(cfg.getRange("B7").getValue()).trim() || "Normal";
  let p1 = toNum(cfg.getRange("C7").getValue());
  let p2 = toNum(cfg.getRange("D7").getValue());
  let correlation = Math.max(0, Math.min(1, toNum(cfg.getRange("E7").getValue())));

  // Dynamic labels + default values
  try {
    if (distribution === "Uniform") {
      cfg.getRange("C6").setValue("Uniform Min");
      cfg.getRange("D6").setValue("Uniform Max");

      if (p1 === 0 && p2 === 0) {
        cfg.getRange("C7").setValue(40);
        cfg.getRange("D7").setValue(60);
        p1 = 40; p2 = 60;
      }

      if (p2 < p1) { const tmp = p1; p1 = p2; p2 = tmp; }
    } else {
      cfg.getRange("C6").setValue("Normal Mean");
      cfg.getRange("D6").setValue("Normal SD");

      if (p1 === 0 && p2 === 0) {
        cfg.getRange("C7").setValue(50);
        cfg.getRange("D7").setValue(20);
        p1 = 50; p2 = 20;
      }

      if (p2 <= 0) p2 = Math.max(1, Math.abs(p1) * 0.2);
    }
  } catch (err) {}

  // -------------------------------
  // TREND (EXPONENTIAL – realistic)
  // -------------------------------
  const dailyGrowth =
    (parseFloat(String(cfg.getRange("B8").getValue()).replace("%", "")) / 100) || 0;

  // ---------------------
  // DAY-OF-WEEK MULTIPLIERS (B10:H10)
  // ---------------------
  const dowRow = cfg.getRange("B10:H10").getValues()[0] || [];
  const dowMultipliers = dowRow.map(v => (v === "" ? 1 : toNum(v) || 1));

  // Map Monday–Sunday → JS Sunday–Saturday
  const dowMap = {
    0: dowMultipliers[6], // Sunday
    1: dowMultipliers[0], // Monday
    2: dowMultipliers[1], // Tuesday
    3: dowMultipliers[2], // Wednesday
    4: dowMultipliers[3], // Thursday
    5: dowMultipliers[4], // Friday
    6: dowMultipliers[5], // Saturday
  };

  // ------
  // EVENTS
  // ------
  const events = [];
  const evRows = cfg.getRange("B13:E16").getValues();
  for (let r of evRows) {
    if (!r[0]) continue;
    const day = toDate(r[0]);
    const dur = Math.max(0, Math.floor(toNum(r[1])));
    const factor = toNum(r[2]);
    const prob = Math.max(0, Math.min(1, toNum(r[3])));
    if (!day || dur <= 0) continue;
    events.push({ day, duration: dur, factor, probability: prob });
  }

  // ----------------
  // RANDOM FUNCTIONS
  // ----------------
  function randNormal(mean, sd) {
    const u = Math.random(), v = Math.random();
    return mean + sd * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  function randUniform(min, max) {
    return min + Math.random() * (max - min);
  }

  function nextRandom() {
    return distribution === "Uniform"
      ? randUniform(p1, p2)
      : randNormal(p1, p2);
  }

  // -------------
  // GENERATE DATA
  // -------------
  const header = ["Date"].concat(mines).concat(["Total"]);
  const result = [header];

  const prev = Array(mineCount).fill(null);

  for (let i = 0; i < daysCount; i++) {
    const d = new Date(startDate);
    d.setDate(d.getDate() + i);

    const row = [d];
    let total = 0;

    const dow = d.getDay();
    const dowMult = dowMap[dow] || 1;

    for (let m = 0; m < mineCount; m++) {
      let val = nextRandom();

      if (!isFinite(val)) val = Math.abs(p1);
      if (val < 0) val = Math.abs(val);

      // Day-of-week effect
      val *= dowMult;

      // Correlation smoothing
      if (prev[m] !== null) {
        val = (1 - correlation) * val + correlation * prev[m];
      }
      prev[m] = val;

      // Exponential trend (realistic)
      val *= Math.pow(1 + dailyGrowth, i);

      // Events
      for (let ev of events) {
        const diff = (d - ev.day) / 86400000;
        if (diff >= 0 && diff <= ev.duration) {
          const x = diff - ev.duration / 2;
          const sigma = Math.max(ev.duration / 4, 0.1);
          const gauss = Math.exp(-(x * x) / (2 * sigma * sigma));
          const mult = 1 + (ev.factor - 1) * gauss;
          if (Math.random() < ev.probability) val *= mult;
        }
      }

      if (!isFinite(val) || val < 0) val = 0;

      row.push(val);
      total += val;
    }

    row.push(total);
    result.push(row);
  }

  // ------------
  // WRITE OUTPUT
  // ------------
  let out = ss.getSheetByName("Generated Data");
  if (!out) out = ss.insertSheet("Generated Data");

  out.clearContents();
  out.getRange(1, 1, result.length, result[0].length).setValues(result);

  // -------------
  // REBUILD CHART
  // -------------
  try {
    cfg.getCharts().forEach(c => cfg.removeChart(c));

    const chartBuilder = cfg.newChart().setChartType(Charts.ChartType.LINE);

    chartBuilder.addRange(out.getRange(1, 1, result.length, 1)); // Date

    for (let col = 0; col < mineCount; col++) {
      chartBuilder.addRange(out.getRange(1, 2 + col, result.length, 1));
    }

    chartBuilder
      .setPosition(18, 2, 0, 0)
      .setOption("title", "Generated Mining Output")
      .setOption("curveType", "function")
      .setOption("legend", { position: "right" })
      .setOption("hAxis", { format: "yyyy-MM-dd" })
      .setNumHeaders(1);

    cfg.insertChart(chartBuilder.build());
  } catch (e) {
    Logger.log("Chart creation failed: " + e);
  }

  ss.toast("Data generated!", "Mining Ops", 3);
}
