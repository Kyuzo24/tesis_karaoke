import csv
from audio.pitch import hz_to_nota

def guardar_csv(ruta_salida, tiempos, frecuencias):
    with open(ruta_salida, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["tiempo", "frecuencia", "nota"])

        for t, f0 in zip(tiempos, frecuencias):
            nota = hz_to_nota(f0) if f0 > 0 else ""
            writer.writerow([t, f0, nota])