from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/filtro_aprendido'
s=json.loads((OUT/'validacion_resumen.json').read_text())
choice=json.loads((OUT/'seleccion.json').read_text())['selected']
keys=['vocadito/voz','mir1k/voz','mdb/voz','mir1k/musica10','mir1k/musica0']
labels=['Vocadito · voz','MIR-1K · voz','MDB · voz','MIR-1K · voz +10 dB','MIR-1K · voz/música 0 dB']
fig,axs=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
y=np.arange(len(keys))
for ax,metric,title,xmax in zip(axs,['pitch_correct_50c_pct','false_voiced_pct'],['Tono correcto · mayor es mejor','Notas falsas · menor es mejor'],[110,22]):
    for v,offset,color,label in [('base',-.17,'#8898ae','Filtro previo'),(choice,.17,'#138582','Filtro aprendido')]:
        vals=[s[k][v][metric] for k in keys]
        bars=ax.barh(y+offset,vals,height=.31,color=color,label=label)
        ax.bar_label(bars,labels=[f'{n:.2f}%' for n in vals],padding=4,fontsize=9)
    ax.set_yticks(y,labels if ax is axs[0] else ['']*len(keys))
    ax.invert_yaxis();ax.set_xlim(0,xmax);ax.set_title(title,fontsize=11)
    ax.set_xlabel('Porcentaje');ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
axs[0].legend(loc='lower right',fontsize=9)
fig.suptitle('Validación reservada: 55 grabaciones · interfaz nueva\nModelo elegido antes de evaluar estas grabaciones',fontsize=13)
fig.savefig(OUT/'validacion.png',dpi=170)
