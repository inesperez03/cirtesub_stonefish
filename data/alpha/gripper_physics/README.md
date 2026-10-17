# Mallas físicas simplificadas de los grippers Alpha

Estas mallas se usan en ambos brazos mediante `cirtesub_alpha_lowpoly.scn`.
El launch `cirtesub_cirtesu_net.launch.py` las carga a través de su escenario
envoltorio. Los archivos originales y el escenario `cirtesub_alpha.scn`
se conservan; las mallas visuales siguen siendo las originales.

| Fuente original | Malla física nueva | Triángulos originales | Triángulos nuevos |
| --- | --- | ---: | ---: |
| `rs1_124_v2.obj` | `rs1_124_phy.obj` | 1.642 | 800 |
| `rs1_130_fin_v3.obj` | `rs1_130_phy.obj` | 12.916 | 2.000 |
| `rs1_139_fin_v3.obj` | `rs1_139_phy.obj` | 14.442 | 2.200 |

Los dos grippers pasan de 58.000 a 10.000 triángulos físicos: reducción del
82,76 %. Las masas explícitas, articulaciones, escalas y orígenes se conservan.
La simplificación no utiliza una envolvente convexa como malla física: se
conservan los huecos para limitar las variaciones de volumen e inercia.

## Generación y comprobaciones

La herramienta offline `tools/simplify_gripper_meshes.py` aplica decimación
cuádrica con Open3D. Calcula en milímetros para mejorar el condicionamiento
numérico y exporta en metros, sin referencias a materiales ni texturas.
Se generaron con Open3D 0.17.0 y Trimesh 4.8.2.

La herramienta requiere versiones compatibles de NumPy, Open3D y Trimesh;
estas dependencias no se necesitan para ejecutar el simulador. Desde la raíz
del paquete, `python3 tools/simplify_gripper_meshes.py` regenera únicamente las
mallas físicas nuevas y `python3 tools/simplify_gripper_meshes.py --check` las
comprueba sin escribir archivos.

Se validaron los OBJ exportados: superficies cerradas, orientación consistente,
ausencia de autointersecciones e inercia definida positiva. La comparación de
superficies es bidireccional e incluye todos los vértices, los centros de todas
las caras y 20.000 muestras uniformes por malla, con semilla 42. Los errores de
superficie siguientes son máximos observados en ese muestreo, no una cota
analítica de toda la superficie.

| Pieza | Superficie (mm) | Límites (mm) | Centro de masa (mm) | Volumen (%) | Inercia por unidad de masa (%) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `rs1_124` | 0,483 | 0,064 | 0,010 | 0,226 | 0,092 |
| `rs1_130` | 0,394 | 0,016 | 0,013 | 0,170 | 0,044 |
| `rs1_139` | 0,453 | 0,021 | 0,010 | 0,161 | 0,030 |

Los límites de aceptación son 0,5 mm para superficie, límites y centro de
masa; 1 % para volumen y 2 % para inercia por unidad de masa.

No se ha medido todavía la mejora de tiempo en simulación. El contacto propio
de `stonefish_net` sigue utilizando cajas redondeadas; reducir estas mallas
no cambia ese algoritmo.
