# naomi-pi-tools — scripts de la Raspberry (WiPi Netbooter) y del PC para trabajar con una NAOMI por NetDIMM

Los scripts que se usan para **enviar una imagen a la placa, medir cómo va y apuntarla en el menú del netbooter**,
reunidos en un sitio. Hasta ahora estaban repartidos por los repos de cada port.

*In English:* helper scripts for a NAOMI + NetDIMM cabinet netbooted from a Raspberry Pi running WiPi Netbooter: send
an image, keep the board's time hack alive, read a running program's live figures over the NetDIMM (no screen
overlay), and add rows to `romsinfo.csv` safely. Code comments are in English, the documents in Spanish.

> **Nada de ROMs, ni BIOS, ni contraseñas.** Aquí solo hay scripts y documentación. La contraseña de la Raspberry se
> pasa por la variable de entorno `PIPASS` y no se escribe en ningún fichero; pídesela al propietario del mueble.

## Qué hay

| Dónde | Fichero | Para qué | Estado |
|---|---|---|---|
| PC | [`pc/pi.py`](pc/pi.py) | Ejecuta un comando en la Raspberry por SSH (paramiko) | ✅ usado a diario |
| PC | [`pc/piput.py`](pc/piput.py) | Copia ficheros a la Raspberry por SFTP | ✅ usado a diario |
| PC | [`pc/send_and_measure.sh`](pc/send_and_measure.sh) | Sube una imagen, la envía a la placa y lee sus cifras en directo | 🧪 versión general de la receta usada; probada sin placa |
| Pi | [`pi/send_game.sh`](pi/send_game.sh) | Envía la imagen a la NetDIMM y deja vivo `timehack.py` (si no, «error 33») | 🧪 ídem |
| Pi | [`pi/live.py`](pi/live.py) | **El lector «live» de todos los proyectos:** lee por la NetDIMM el bloque de datos del programa en marcha y lo reconoce por su firma: naomi-kit (`NKLV`), mame4all-naomi (`MAME`), Daytona nativo (`NEST`) y programas de KallistiOS con el parche `NAOMI_HOST` de dc2naomi (`LIVE`, Mario Kart 64); cualquier otro con `--fields`. Cifras por segundo, consola, palabras sueltas | 🧪 unificado el 2026-11-13 y probado con una NetDIMM simulada; los cinco lectores de los que sale sí se usaron en placa |
| Pi | [`pi/add_romsinfo_rows.py`](pi/add_romsinfo_rows.py) | Añade filas a `romsinfo.csv` con copia previa y sin pegarlas a la anterior | 🧪 probado con un CSV de mentira |

✅ funciona en placa · 🧪 sin probar en la placa real todavía (los scripts nuevos se probaron sin ella).

La **VMU en ficheros** de los juegos de Dreamcast (`dc2naomi_send.py` y `dc2naomi_vmu.py`) sigue en su sitio:
[dc2naomi/wipi](https://github.com/0skarzer0/dc2naomi/tree/main/wipi). `send_game.sh` los usa si están instalados.

## Empezar

Desde el PC, con la Raspberry en la red (en el mueble de este proyecto: `192.168.68.60`, que ve la NetDIMM en `10.0.0.4`):

```bash
pip install paramiko
export PIHOST=192.168.x.y      # la Raspberry
export PIPASS=...              # nunca en un fichero
python3 pc/pi.py 'ls /boot/roms | head'

# enviar una imagen de prueba y leer 12 s de cifras en directo
NETDIMM=10.0.0.4 pc/send_and_measure.sh test.bin.gz 0x8c357fe8 12
```

`0x8c357fe8` es la dirección del bloque de cifras del programa; cambia con cada compilación
(`sh-elf-nm programa.elf | grep naomi_live`). Cómo funciona: [docs/telemetria-netdimm.md](docs/telemetria-netdimm.md).

Para apuntar un juego en el menú del netbooter, en la Raspberry:

```bash
python3 add_romsinfo_rows.py filas.csv      # copia previa + añade + salta las repetidas
```

y luego importarlo a la web (ver [docs/trampas.md](docs/trampas.md)).

## Documentos

| Documento | Qué hay |
|---|---|
| [docs/telemetria-netdimm.md](docs/telemetria-netdimm.md) | Cómo leer la memoria de un programa en marcha por la NetDIMM: protocolo, direcciones, errores |
| [docs/trampas.md](docs/trampas.md) | Lo que ya ha dado problemas: «error 33», `pkill -f`, CSV sin salto de línea, `.bin` sin comprimir… |
| [HANDOFF.md](HANDOFF.md) | Estado y siguientes pasos, para retomar el trabajo en otra sesión |

## Dónde encaja

Es la parte de «la Raspberry» de [naomi-wheel-games](https://github.com/0skarzer0/naomi-wheel-games) (índice del
proyecto). Los datos del mueble (JVS, trampas del hardware real) están en
[crazytaxi_cabinet_info](https://github.com/0skarzer0/crazytaxi_cabinet_info). El código que contesta a las lecturas
por la NetDIMM está en los ports: `src/naomi/naomi_dimmcomms.cpp` en
[mame4all-naomi](https://github.com/0skarzer0/mame4all-naomi) y en el residente de
[dc2naomi](https://github.com/0skarzer0/dc2naomi).

## Agradecimientos

- **[WiPi Netbooter](https://github.com/chunksin/WiPiNetbooter)** (chunksin y colaboradores) y **Piforce**: el
  netbooter donde corren estos scripts (`/sbin/piforce`, `timehack.py`, `importcsv.py`).
- **[DragonMinded](https://github.com/DragonMinded)**: sus [herramientas de netboot](https://github.com/DragonMinded/netboot)
  (`netdimm.py`, que `live.py` usa para leer la memoria) y [libnaomi](https://github.com/DragonMinded/libnaomi), cuyo
  `dimmcomms.c` define el protocolo de peticiones de la NetDIMM.
- **[paramiko](https://www.paramiko.org/)**, para el SSH/SFTP de `pi.py` y `piput.py`.
- **Claude** (Anthropic), a través de Claude Code: estos scripts se han escrito y depurado con Claude en sesiones con
  el propietario del mueble, que es quien prueba cada cosa en la placa.

Las licencias de cada proyecto citado siguen siendo las suyas.
