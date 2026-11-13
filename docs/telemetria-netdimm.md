# Leer un programa en marcha por la NetDIMM («live»)

Sirve para **ver los fps y los tiempos de un port mientras se juega, sin poner nada en pantalla**. En los ports de
este proyecto se midió así todo lo de Super Sprint (por ejemplo, que 64 KB de búfer de vértices daban 5 fps en placa y
con 512 KB, 60).

## Cómo funciona

1. La NetDIMM permite desde la red **leer y escribir la memoria de la NAOMI** (`peek` / `poke` de 8, 16 y 32 bits). Lo
   hace la Raspberry con `netdimm.py` de DragonMinded (`/sbin/piforce/dm_netboot`).
2. **El programa de la placa tiene que contestar esas peticiones.** El protocolo es el de `dimmcomms.c` de
   [libnaomi](https://github.com/DragonMinded/libnaomi). En los ports de este proyecto
   (`src/naomi/naomi_dimmcomms.cpp`) un hilo mira el bit 3 de `ISTEXT` cada 2 ms y atiende la petición, solo sobre
   memoria segura (RAM, Holly, AICA, VRAM, registros del SH-4).
   Un juego de NAOMI normal ya contesta. **Un programa que no lo hace tarda 17–30 s en responder y devuelve basura**
   (en las pruebas con el residente de dc2naomi pasó hasta que se añadió `dimm_service()`).
3. El programa guarda cada segundo un **bloque de palabras de 32 bits** en una variable global (en mame4all-naomi,
   `naomi_live`, struct `naomi_live_t` de `src/naomi/naomi.h`): segundos, fps emulados y mostrados, % de ocupación,
   tiempos por CPU emulada, sonido, vídeo… La primera palabra es una «firma» (`0x454d414d` = «MAME») para saber que
   se está leyendo el bloque y no otra cosa.
4. `pi/live.py` lee ese bloque cuatro veces por segundo y escribe una línea por segundo.

## Usarlo

```bash
# 1. dirección del bloque: cambia con cada compilación
sh-elf-nm programa.elf | grep naomi_live        # 8c357fe8 D _naomi_live

# 2. desde el PC: sube, envía y lee 12 s
NETDIMM=10.0.0.4 pc/send_and_measure.sh imagen.bin.gz 0x8c357fe8 12
```

o, ya en la Raspberry con el juego en marcha: `python3 live.py 10.0.0.4 0x8c357fe8 60`.

Ejemplo de salida (Super Sprint, tiempos en ms por frame emulado):

```
seconds 59 emulated 60 shown 60 busy 74 game_loops 29 cpu0 7.1 cpu1 1.0 cpu2 0.0 sound 1.4 video 1.0 upload 0.0 ...
```

## Con otro programa

Define tu propio bloque de palabras de 32 bits en una variable global (la firma en la primera), contesta a las
peticiones con `dimmcomms` y llama a `live.py` con tus nombres de campo:

```bash
python3 live.py 10.0.0.4 0x8c100000 20 --fields magic,frame,fps --magic 0x12345678
```

Si un campo se llama `seconds`, `live.py` imprime solo cuando cambia (una vez por segundo). Los campos `cpu0`, `cpu1`,
`cpu2`, `sound`, `video` y `upload` se muestran en ms, porque el bloque de mame4all-naomi los guarda en décimas de ms.

## Cosas que ya han dado guerra

- **La dirección:** la NetDIMM ve la RAM sin los bits de caché (`0x8c...` → `& 0x01ffffff`); `live.py` ya lo hace, pero
  si miras con otra herramienta, quita el `0x8c000000`.
- **Guarda el `nm` de cada imagen de prueba**: sin él no sabes qué dirección leer ni qué variable es cuál.
- **No consultes una imagen recién enviada antes de que arranque:** si «no live block» aparece en los primeros
  segundos, espera; `send_and_measure.sh` espera 25 s tras el envío.
- **Mide en la placa real, no en Flycast:** los núcleos de CPU emulados van 2–3,5 veces más lentos en el SH-4 real
  (ver [crazytaxi_cabinet_info](https://github.com/0skarzer0/crazytaxi_cabinet_info)).
