#!/usr/bin/env python3
"""Generate or check the gripper physics meshes without changing the visual assets.

Offline dependencies: numpy, open3d and trimesh. They are not needed by the simulator.
Run with --check to validate the existing generated meshes without writing files.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import open3d as o3d
import trimesh


DATA = Path(__file__).resolve().parents[1] / 'data' / 'alpha'
PARTS = (
    ('rs1_124_v2.obj', 'rs1_124_phy.obj', 800),
    ('rs1_130_fin_v3.obj', 'rs1_130_phy.obj', 2000),
    ('rs1_139_fin_v3.obj', 'rs1_139_phy.obj', 2200),
)


def load_mesh(path):
    mesh = o3d.io.read_triangle_mesh(str(path), enable_post_processing=False)
    mesh.remove_duplicated_vertices()
    mesh.remove_degenerate_triangles()
    mesh.remove_duplicated_triangles()
    if not len(mesh.triangles):
        raise ValueError(f'{path}: empty mesh')
    return mesh


def mass_properties(mesh):
    return trimesh.Trimesh(
        vertices=np.asarray(mesh.vertices).copy(),
        faces=np.asarray(mesh.triangles).copy(),
        process=False,
    )


def sample_surface(mesh):
    # Include every vertex and face centre as well as repeatable surface samples.
    o3d.utility.random.seed(42)
    vertices = np.asarray(mesh.vertices)
    centres = vertices[np.asarray(mesh.triangles)].mean(axis=1)
    samples = np.asarray(mesh.sample_points_uniformly(20000).points)
    return np.vstack((vertices, centres, samples))


def distances_to_surface(mesh, points):
    # Materials and UVs are irrelevant to geometric distance queries.
    tensor_mesh = o3d.t.geometry.TriangleMesh(
        o3d.core.Tensor(np.asarray(mesh.vertices), dtype=o3d.core.Dtype.Float32),
        o3d.core.Tensor(np.asarray(mesh.triangles), dtype=o3d.core.Dtype.Int64),
    )
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(tensor_mesh)
    return scene.compute_distance(
        o3d.core.Tensor(points, dtype=o3d.core.Dtype.Float32),
    ).numpy()


def validate(original, candidate, target):
    before = mass_properties(original)
    after = mass_properties(candidate)
    if not original.is_watertight() or not before.is_winding_consistent:
        raise ValueError('Source mesh must be closed, manifold and consistently oriented')
    if not candidate.is_watertight() or not after.is_winding_consistent:
        raise ValueError('Simplified mesh is open, non-manifold or self-intersecting')
    if after.volume <= 0 or before.volume <= 0:
        raise ValueError('Mesh must have positive signed volume')
    if len(candidate.triangles) > target:
        raise ValueError('Triangle budget exceeded')

    volume_error = abs(after.volume / before.volume - 1)
    bounds_error = np.abs(after.bounds - before.bounds).max()
    centre_error = np.linalg.norm(after.center_mass - before.center_mass)
    # Explicit masses in the scenario remain unchanged: compare inertia per unit mass.
    before_inertia = before.moment_inertia / before.mass
    after_inertia = after.moment_inertia / after.mass
    inertia_error = np.linalg.norm(after_inertia - before_inertia) / np.linalg.norm(before_inertia)
    forward = distances_to_surface(candidate, sample_surface(original))
    backward = distances_to_surface(original, sample_surface(candidate))
    surface_error = max(forward.max(), backward.max())
    if surface_error > 0.0005 or bounds_error > 0.0005 or centre_error > 0.0005:
        raise ValueError(
            f'Geometric deviation exceeds 0.5 mm: surface={surface_error * 1000:.6f}, '
            f'bounds={bounds_error * 1000:.6f}, centre={centre_error * 1000:.6f}',
        )
    if volume_error > 0.01 or inertia_error > 0.02:
        raise ValueError(
            f'Volume deviation exceeds 1% or inertia deviation exceeds 2%: '
            f'volume={volume_error * 100:.6f}%, inertia={inertia_error * 100:.6f}%',
        )
    if not np.isfinite(after.moment_inertia).all() or np.linalg.eigvalsh(after_inertia).min() <= 0:
        raise ValueError('Invalid inertia tensor')

    return {
        'source_triangles': len(original.triangles),
        'physics_triangles': len(candidate.triangles),
        'physics_vertices': len(candidate.vertices),
        'sampled_surface_error_mm': round(float(surface_error) * 1000, 6),
        'bounds_error_mm': round(float(bounds_error) * 1000, 6),
        'centre_of_mass_error_mm': round(float(centre_error) * 1000, 6),
        'volume_error_percent': round(float(volume_error) * 100, 6),
        'inertia_per_mass_error_percent': round(float(inertia_error) * 100, 6),
    }


def write_obj(path, mesh, source):
    # Geometry only: no material or texture dependencies for the physical model.
    lines = [f'# Simplified physics mesh from {source}; coordinates in metres.']
    lines.extend('v {:.12g} {:.12g} {:.12g}'.format(*v) for v in np.asarray(mesh.vertices))
    lines.extend('f {} {} {}'.format(*(face + 1)) for face in np.asarray(mesh.triangles))
    path.write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate existing meshes without writing')
    args = parser.parse_args()
    results = {}
    for source, output, target in PARTS:
        original = load_mesh(DATA / source)
        destination = DATA / 'gripper_physics' / output
        if args.check:
            candidate = load_mesh(destination)
            results[output] = validate(original, candidate, target)
            continue

        # Millimetres keep the quadric calculation well-conditioned for these small parts.
        working = o3d.geometry.TriangleMesh(original)
        working.scale(1000, center=(0, 0, 0))
        candidate = working.simplify_quadric_decimation(target)
        candidate.scale(0.001, center=(0, 0, 0))
        # Match the precision of Stonefish's mesh vertices and the OBJ loader.
        candidate.vertices = o3d.utility.Vector3dVector(
            np.asarray(candidate.vertices).astype(np.float32).astype(np.float64),
        )
        candidate.remove_duplicated_vertices()
        candidate.remove_degenerate_triangles()
        candidate.remove_duplicated_triangles()
        validate(original, candidate, target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_obj(destination, candidate, source)
        # Validate the exported geometry, not just the in-memory candidate.
        results[output] = validate(original, load_mesh(destination), target)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
