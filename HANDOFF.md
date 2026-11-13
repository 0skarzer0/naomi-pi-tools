# HANDOFF — naomi-pi-tools

Para retomar el trabajo en otra sesión (persona o IA). Lee antes el [README](README.md) y [docs/trampas.md](docs/trampas.md).

## Estado (2026-11-13)

Repositorio recién creado con lo que estaba repartido por los repos de los ports. Sin historial anterior aquí.

| Pieza | Origen | Estado |
|---|---|---|
| `pc/pi.py`, `pc/piput.py` | `tools/board/` de dc2naomi y el PC del usuario | ✅ idénticos en función; solo se añadió el uso y salir con el código del comando |
| `pi/live.py` | `naomi/tools/live.py` de mame4all-naomi (y su idea, del `live.py` del port nativo de Daytona) | 🧪 generalizado (campos y firma por parámetro); probado con una NetDIMM simulada, no en la placa |
| `pi/send_game.sh`, `pc/send_and_measure.sh` | la receta que se escribía a mano en `/root/sendtest.sh` y `hw.sh` | 🧪 mismos pasos; no ejecutados en la placa tal como están aquí |
| `pi/add_romsinfo_rows.py` | el arreglo del CSV sin salto de línea | 🧪 probado con un CSV de mentira |

## Decisiones

- **Contraseñas:** nunca en el repo. `PIHOST` y `PIPASS` por entorno; los documentos dicen «pídesela al propietario».
- **VMU en ficheros:** no se copió aquí; sigue en [dc2naomi/wipi](https://github.com/0skarzer0/dc2naomi/tree/main/wipi)
  para no tener dos copias que se desincronicen. `send_game.sh` usa `dc2naomi_send.py` si está instalado.
- **WiPi/Piforce** (`timehack.py`, `importcsv.py`, `netdimm.py`) no se redistribuyen: son de otros autores y ya
  están en el netbooter.
- **`naomi-kit`** (la librería de los ports nativos) ya tiene scripts de la Pi; este repo no los sustituye. Pendiente de
  revisar cuáles se solapan (ver abajo).

## Siguientes pasos

1. **Probar en la placa** `send_and_measure.sh` y `send_game.sh` completos, y marcar ✅ en el README.
2. **Comprobar `importcsv.py`** (argumentos) y, si es seguro, que `add_romsinfo_rows.py` lo llame con `--import`.
3. **Solapes con `naomi-kit`:** su `tools/pi/live.py` (la guía de contribuciones de naomi-wheel-games lo cita) probablemente solapa con `pi/live.py`; no lo he comparado. Decidir cuál queda (lo razonable: el del kit,
   y este repo enlazarlo) para no mantener dos.
4. **Prueba automática de rendimiento:** enviar una imagen, leer N segundos de `live.py` y escribir la fila de
   `docs/pi60-juegos.md` de naomi-wheel-games con fecha y fps medidos (hoy se copia a mano).
5. **Medir el tiempo de envío** por tamaño de imagen y ajustar `WAIT_SEND` solo, leyendo el registro de envío en vez de
   esperar un tiempo fijo.
6. **Licencia:** la elige el propietario del mueble; todavía no hay `LICENSE`.

## Reglas del proyecto (resumen)

Nada de ROMs, BIOS ni datos derivados; documentar cada operación; agradecer todo lo usado; lo no probado en placa se
marca 🧪 con su fecha. Detalle: [CONTRIBUTING de naomi-wheel-games](https://github.com/0skarzer0/naomi-wheel-games/blob/main/CONTRIBUTING.md).
