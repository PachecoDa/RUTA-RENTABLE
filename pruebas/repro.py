"""Prueba de reproducibilidad: ejecuta los notebooks 01-04 del paquete entregado en una copia limpia
y compara sus salidas con los archivos entregados."""
import sys, shutil, hashlib, json, time
from pathlib import Path
import nbformat
from nbclient import NotebookClient
import pandas as pd, numpy as np, joblib

PKG = Path(sys.argv[1])          # .../6. ENTREGABLE FINAL/entrega_final
T = Path(sys.argv[2])            # carpeta temporal
if T.exists(): shutil.rmtree(T)
(T / 'datos').mkdir(parents=True); (T / 'notebooks').mkdir()
for f in (PKG / 'datos' / 'crudos').glob('*.gz'):
    shutil.copy(f, T / 'datos' / f.name)
for n in ['01_limpieza', '02_cruce_rndc_sicetac', '03_modelamiento']:
    shutil.copy(PKG / 'notebooks' / f'{n}.ipynb', T / 'datos' / f'{n}.ipynb')
shutil.copy(PKG / 'notebooks' / '04_modelo_final.ipynb', T / 'notebooks' / '04_modelo_final.ipynb')

def run(nb_path, cwd):
    t = time.time()
    nb = nbformat.read(nb_path, 4)
    try:
        NotebookClient(nb, timeout=2400, kernel_name='python3', resources={'metadata': {'path': str(cwd)}}).execute()
        ok = True
    except Exception as e:
        ok = False; print('  ERROR', type(e).__name__, str(e)[:300])
    print(f'{nb_path.name}: {"OK" if ok else "FALLÓ"} en {time.time()-t:.0f} s', flush=True)
    return ok

md5 = lambda p: hashlib.md5(Path(p).read_bytes()).hexdigest()
res = {}
for n in ['01_limpieza', '02_cruce_rndc_sicetac', '03_modelamiento']:
    res[n] = run(T / 'datos' / f'{n}.ipynb', T / 'datos')
res['04'] = run(T / 'notebooks' / '04_modelo_final.ipynb', T / 'notebooks')

print('\n== Comparación con lo entregado')
for f in ['dataset_modelo_dic2025.csv', 'dataset_auditoria_dic2025.csv', 'conjunto_prueba_reservado.csv',
          'bitacora_limpieza.csv', 'bitacora_cruce.csv', 'sicetac_costos_c2_dic2025.csv']:
    a, b = T / 'datos' / f, PKG / 'datos' / f
    if a.exists():
        same = md5(a) == md5(b)
        if not same:
            da, db = pd.read_csv(a), pd.read_csv(b)
            same = da.shape == db.shape and da.round(6).equals(db.round(6))
            print(f'{f}: {"IDÉNTICO (contenido)" if same else f"DIFERENTE {da.shape} vs {db.shape}"}')
        else:
            print(f'{f}: IDÉNTICO (byte a byte)')
    else:
        print(f'{f}: NO SE GENERÓ')
for f in ['tabla_comparacion.csv', 'tabla_umbrales.csv', 'tabla_splines.csv']:
    a, b = T / 'datos' / f, PKG / 'resultados' / 'entrega2' / f
    if a.exists():
        da, db = pd.read_csv(a), pd.read_csv(b)
        num = da.select_dtypes('number').columns
        d = (da[num] - db[num]).abs().max().max()
        print(f'{f}: diferencia numérica máxima {d:.2e}')
for f in ['tabla_decision_modelo.csv', 'tabla_umbrales_costo.csv', 'tabla_prueba_final.csv']:
    a, b = T / 'resultados' / f, PKG / 'resultados' / 'entrega_final' / f
    if a.exists():
        da, db = pd.read_csv(a), pd.read_csv(b)
        num = da.select_dtypes('number').columns
        d = (da[num] - db[num]).abs().max().max()
        print(f'{f}: diferencia numérica máxima {d:.2e}')
    else:
        print(f'{f}: NO SE GENERÓ')
ma, mb = T / 'app' / 'modelo_final.joblib', PKG / 'app' / 'modelo_final.joblib'
if ma.exists():
    te = pd.read_csv(PKG / 'datos' / 'conjunto_prueba_reservado.csv')
    X = te[['KILOMETROS', 'KILOGRAMOS', 'CAPITULO', 'NATURALEZACARGA', 'DEPARTAMENTOORIGEN', 'DEPARTAMENTODESTINO']]
    pa, pb = joblib.load(ma).predict_proba(X)[:, 0], joblib.load(mb).predict_proba(X)[:, 0]
    print(f'Modelo re-entrenado vs entregado: diferencia máxima de probabilidad {np.abs(pa - pb).max():.2e}')
    ja = json.load(open(T / 'app' / 'metadatos.json', encoding='utf-8')); jb = json.load(open(PKG / 'app' / 'metadatos.json', encoding='utf-8'))
    print('Umbral costo:', ja['umbral_costo'], 'vs', jb['umbral_costo'], '| AUC prueba:', round(ja['auc_prueba'], 4), 'vs', round(jb['auc_prueba'], 4))
print('\nResumen ejecución:', res)
