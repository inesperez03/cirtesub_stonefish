# Mallas físicas simplificadas de los brazos Alpha

Se usan en los diez eslabones de ambos brazos mediante
`cirtesub_alpha_lowpoly.scn`, que carga el launch
`cirtesub_cirtesu_net.launch.py`. Las mallas originales y el escenario
`cirtesub_alpha.scn` permanecen intactos. Los modelos visuales siguen siendo
los originales; se mantienen articulaciones, escalas, orígenes y masas
explícitas del robot.

| Fuente original | Malla física | Triángulos originales | Nuevos | Usos |
| --- | --- | ---: | ---: | ---: |
| `m3_inline.obj` | `m3_inline_phy.obj` | 2.436 | 1.100 | 1 |
| `m3_inline2.obj` | `m3_inline2_phy.obj` | 2.436 | 1.100 | 1 |
| `m2_1_1_v2.obj` | `m2_1_1_phy.obj` | 1.142 | 400 | 2 |
| `m2_v2.obj` | `m2_phy.obj` | 1.388 | 500 | 2 |
| `m2_1_3_fin.obj` | `m2_1_3_phy.obj` | 1.142 | 400 | 2 |
| `rs1_v2.obj` | `rs1_phy.obj` | 1.446 | 1.000 | 2 |

Los eslabones pasan de 15.108 a 6.800 triángulos físicos, un 54,99 % menos.
Incluyendo los grippers ya optimizados, ambos brazos pasan de 25.108 a
16.800 triángulos físicos, un 33,09 % menos. Son reducciones de geometría,
no mediciones de FPS ni de tiempo de simulación.

## Validación para Stonefish

Stonefish construye una envolvente convexa para la colisión rígida de cada
`Polyhedron`, pero utiliza su superficie física para calcular propiedades
de masa y fuerzas. Por eso se comparan tanto las envolventes de colisión
como el volumen firmado, centro de masa e inercia de la geometría.

La simplificación permite eliminar detalle de la superficie física que no
define la envolvente de colisión. Se exige un error máximo muestreado de
0,5 mm en la envolvente convexa, límites y centro de masa; 2 mm en la
superficie física completa; 1 % en volumen y 2 % en inercia, tanto por
unidad de masa como a densidad fija. Esta última comprobación también
cubre los eslabones cuya masa se obtiene del volumen y del material.
Los errores de superficie son muestreos bidireccionales con todos los
vértices, centros de caras y 20.000 puntos por superficie, con semilla 42;
no son cotas analíticas de toda la superficie.

Los resultados exportados están en `validation.json`. El error máximo
observado en las envolventes es 0,479 mm, el de volumen 0,289 % y el de
inercia a densidad fija 0,940 %. Las envolventes convexas son cerradas y
válidas, y las superficies orientadas no tienen bordes abiertos ni flujos
de aristas sin compensar. No hay triángulos degenerados ni inercias no
definidas positivas.

Estas mallas no constituyen una reparación integral del CAD. Las fuentes
`m3_inline` contienen 48 pares de triángulos que se intersecan, y `rs1_v2`
contiene 169. En las versiones físicas quedan 4 y 154 respectivamente;
además, cada M3 simplificado tiene cinco aristas no manifold. Se comprueba
que no aumente el número de pares que se intersecan, pero esto no demuestra
que cada intersección restante sea la misma que en el original. Las
superficies se validan como superficies orientadas cerradas, con volumen
firmado e inercia coherentes; las envolventes convexas de colisión sí son
manifold. Los modelos visuales no se alteran.

## Herramienta offline

`tools/simplify_arm_meshes.py` reutiliza las utilidades geométricas de
`simplify_gripper_meshes.py`. Aplica decimación cuádrica en milímetros y
exporta OBJ en metros, sin materiales ni texturas. Se generaron con
Open3D 0.17.0 y Trimesh 4.8.2.

Desde la raíz del paquete, `python3 tools/simplify_arm_meshes.py` regenera
solo estas mallas y el informe; `python3 tools/simplify_arm_meshes.py --check`
las valida sin escribir archivos. Requiere versiones compatibles de NumPy,
SciPy, Open3D y Trimesh; no añade dependencias al simulador.

La mejora de rendimiento debe medirse en ejecución. El contacto específico
de `stonefish_net` sigue usando cajas redondeadas y no cambia con estas
mallas.
