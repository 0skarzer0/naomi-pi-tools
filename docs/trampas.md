# Trampas conocidas del netbooter y de estos scripts

Cada una salió de un fallo real en el mueble. Si encuentras otra, añádela aquí con su fecha.

## «Error 33 — Gateway is not found» a los pocos minutos de enviar un juego

La placa se reinicia sola con ese mensaje. **Una causa conocida: `timehack.py` (de WiPi Netbooter) no estaba corriendo.**
Un script que lo paraba para enviar el juego no lo volvía a arrancar (dc2naomi, 2026-11-10). `pi/send_game.sh` lo relanza
al terminar el envío, y por eso no vuelve nunca: lánzalo en segundo plano (`nohup … &`). Si el error aparece con un
`timehack.py` vivo, es otra causa y no está diagnosticada.

## `pkill -f` y `pgrep -f` se encuentran a sí mismos

El patrón también casa con la propia orden `bash -c '…'` que lo contiene, y el script se mata a sí mismo. Escribe el
patrón con corchetes (`pkill -f "[t]imehack.py"`) o pon la orden en un fichero `.sh` aparte, como hace `send_game.sh`.

## `romsinfo.csv` no acaba en salto de línea

Si añades una fila con `>>`, se pega a la última. `pi/add_romsinfo_rows.py` lo arregla, hace una copia con fecha
(`romsinfo.csv.bak_…`) y salta las filas ya presentes. Si solo vas a dar filas a otra persona, dáselas **sueltas**, no el
CSV entero.

## Importar el CSV a la web de WiPi

El menú web lee su propia copia (`/var/www/html/csv/romsinfo.csv`). Tras editar `/boot/config/romsinfo.csv`, se importa
con `/sbin/piforce/importcsv.py`, que solo copia su primer argumento al segundo (comprobado su código el 2026-11-19):
`python3 /sbin/piforce/importcsv.py /boot/config/romsinfo.csv /var/www/html/csv/romsinfo.csv`.

## Las imágenes tienen que ser `.bin.gz`

WiPi lee los últimos 4 bytes del fichero como tamaño original del gzip: con un `.bin` sin comprimir falla. El nombre
del `.gz` es el que va en `romsinfo.csv` (`romname` y `audit_name`); **al sustituir una imagen, conserva el nombre** y
no hace falta tocar el CSV.

## Montar `/boot` para escribir

Si `cp` a `/boot/roms` da «Read-only file system»: `mount -o remount,rw /boot` y, al acabar, `sync`.

## La Raspberry no contesta por SSH

Pasa si el mueble o la Raspberry están apagados o en otra red (un `TimeoutError` en `pi.py`). No lo reintentes en bucle:
comprueba que está encendida y su dirección. La NetDIMM (`10.0.0.x`) solo se ve **desde** la Raspberry.

## Envíos largos

Un homebrew pequeño (1,3 MB) tarda unos 45 s en enviarse; un juego de Dreamcast convertido, minutos (Crazy Taxi 2: 49 s;
un disco entero de cientos de MB, bastante más). Sube `WAIT_SEND` en `send_and_measure.sh`. Una Raspberry Pi 3B+ tarda
unos 4 minutos en preparar con `addvmu_stream.py` la VMU de una imagen grande (hazlo en la propia Raspberry).

## Probar mandos en Flycast

Sin `FC_PEDALS=1` el acelerador y el freno están a media carrera y START puede contar como «usado». Es del lado de
Flycast, no de la placa.
