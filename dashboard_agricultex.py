const ESTANDARES = {
  3: 6.3, 4: 8.3, 5: 10.6, 6: 13.3, 7: 16.6,
  8: 20.6, 9: 25.1, 10: 30.0, 11: 35.4
};

const ID_SHEET_DESTINO = '1MPwyjUpHgwbuqqGwzGi1CgCBoEziNdqe5yKEj5PJKtM';

function sincronizarDashboard() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetRecria = ss.getSheetByName('Recria');
  var datos = sheetRecria.getDataRange().getValues();

  var COL_LOTE = 2;
  var COL_SEMANA = 3;
  var COL_LECHON = 4;
  var COL_PESO = 5;

  var grupos = {};
  for (var i = 1; i < datos.length; i++) {
    var fila = datos[i];
    var lote = fila[COL_LOTE];
    var semana = fila[COL_SEMANA];
    var lechon = fila[COL_LECHON];
    var peso = fila[COL_PESO];
    if (lote === '' || semana === '' || peso === '' || peso === null) continue;
    var key = lote + '_' + semana;
    if (!grupos[key]) grupos[key] = { lote: lote, semana: semana, lechones: {} };
    grupos[key].lechones[lechon] = Number(peso);
  }

  var filasDash = [];
  var keys = Object.keys(grupos).sort(function(a, b) {
    var pa = a.split('_'); var pb = b.split('_');
    return (Number(pa[0]) - Number(pb[0])) || (Number(pa[1]) - Number(pb[1]));
  });

  keys.forEach(function(key) {
    var g = grupos[key];
    var pesos = Object.values(g.lechones);
    var n = pesos.length;
    var media = pesos.reduce(function(a, b) { return a + b; }, 0) / n;
    var desvio = n > 1
      ? Math.sqrt(pesos.reduce(function(s, x) { return s + Math.pow(x - media, 2); }, 0) / (n - 1))
      : '';
    var se = n > 1 ? desvio / Math.sqrt(n) : 0;
    var tCrit = n >= 30 ? 1.96 : n >= 10 ? 2.228 : n >= 5 ? 2.776 : n >= 4 ? 3.182 : n >= 3 ? 4.303 : n >= 2 ? 12.706 : 0;
    var icInf = n > 1 ? media - tCrit * se : media;
    var icSup = n > 1 ? media + tCrit * se : media;
    var std = ESTANDARES[g.semana];
    var estado = '';
    if (std) {
      if (icInf > std) estado = '⬆️ Por encima';
      else if (icSup < std) estado = '⚠️ Por debajo';
      else estado = '✅ Dentro';
    }
    filasDash.push([
      g.lote, g.semana, n,
      Math.round(media * 1000) / 1000,
      desvio !== '' ? Math.round(desvio * 1000000) / 1000000 : '',
      Math.round(se * 1000000) / 1000000,
      n > 1 ? Math.round(icInf * 100000) / 100000 : media,
      n > 1 ? Math.round(icSup * 100000) / 100000 : media,
      estado
    ]);
  });

  var encabezadoInfo = [
    ['AGRICULTEX - Dashboard Recria', '', '', '', '', '', '', '', ''],
    ['Estadisticas agregadas por banda y semana. Sin datos individuales.', '', '', '', '', '', '', '', ''],
    ['VALORES ESTANDAR DE REFERENCIA (kg)', '', '', '', '', '', '', '', ''],
    ['Sem 3', 'Sem 4', 'Sem 5', 'Sem 6', 'Sem 7', 'Sem 8', 'Sem 9', 'Sem 10', 'Sem 11'],
    [6.3, 8.3, 10.6, 13.3, 16.6, 20.6, 25.1, 30.0, 35.4],
    ['ESTADISTICAS AGREGADAS POR BANDA Y SEMANA', '', '', '', '', '', '', '', ''],
    ['Lote', 'Semana', 'N (lechones)', 'Media (kg)', 'Desvío S', 'Error Est. (SE)', 'IC 95% inf', 'IC 95% sup', 'Estado vs Estándar']
  ];

  var todasFilas = encabezadoInfo.concat(filasDash);
  todasFilas.push(['IC calculado con t de Student (gl=n-1, a=0.05).', '', '', '', '', '', '', '', '']);

  var sheetDestino = SpreadsheetApp.openById(ID_SHEET_DESTINO).getSheetByName('Hoja 1');
  sheetDestino.clearContents();
  sheetDestino.getRange(1, 1, todasFilas.length, 9).setValues(todasFilas);

  Logger.log('Dashboard sincronizado: ' + filasDash.length + ' filas.');
}

function doGet() {
  sincronizarDashboard();
  return ContentService.createTextOutput('OK');
}
