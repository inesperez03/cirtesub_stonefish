#!/usr/bin/env python3
"""Generate/check Alpha arm physics meshes, keeping the original visual assets.

Offline dependencies: NumPy, SciPy, Open3D and Trimesh. The arm CAD contains
intersecting shells, so validation targets Stonefish's convex collision envelope
and signed mass properties rather than requiring a manifold CAD model.
"""

import argparse
import json
import numpy as np
import open3d as o3d

from simplify_gripper_meshes import (
    DATA, distances_to_surface, load_mesh, mass_properties, sample_surface, write_obj,
)


PARTS = (
    ('m3_inline.obj', 'm3_inline_phy.obj', 1100),
    ('m3_inline2.obj', 'm3_inline2_phy.obj', 1100),
    ('m2_1_1_v2.obj', 'm2_1_1_phy.obj', 400),
    ('m2_v2.obj', 'm2_phy.obj', 500),
    ('m2_1_3_fin.obj', 'm2_1_3_phy.obj', 400),
    ('rs1_v2.obj', 'rs1_phy.obj', 1000),
)
OUTPUT = DATA / 'arm_physics'


def closed_surface(mesh):
    """Check the oriented surface, including CAD shells touching along an edge."""
    shape = mass_properties(mesh)
    faces = np.asarray(mesh.triangles)
    vertices = np.asarray(mesh.vertices)
    if not np.isfinite(vertices).all():
        raise ValueError('Non-finite mesh coordinates')
    if not len(faces) or faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError('Invalid triangle indices')
    triangles = vertices[faces]
    areas = np.linalg.norm(
        np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]),
        axis=1,
    ) / 2
    if areas.min() <= 1e-14:
        raise ValueError('Degenerate triangle')
    edges = shape.edges
    _, inverse, counts = np.unique(
        np.sort(edges, axis=1), axis=0, return_inverse=True, return_counts=True,
    )
    balance = np.bincount(
        inverse, weights=np.where(edges[:, 0] < edges[:, 1], 1, -1),
    )
    if (counts < 2).any() or (balance != 0).any():
        raise ValueError('Open or inconsistently oriented surface')
    if shape.volume <= 0:
        raise ValueError('Non-positive signed volume')
    return shape, int((counts > 2).sum())


def convex_mesh(shape):
    hull = shape.convex_hull
    return o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(hull.vertices),
        o3d.utility.Vector3iVector(hull.faces),
    )


def surface_error(first, second):
    forward = distances_to_surface(second, sample_surface(first))
    backward = distances_to_surface(first, sample_surface(second))
    return float(max(forward.max(), backward.max()))


def validate(original, candidate, target):
    before, _ = closed_surface(original)
    after, non_manifold_edges = closed_surface(candidate)
    if len(candidate.triangles) > target:
        raise ValueError('Triangle budget exceeded')
    # Several sources contain overlapping CAD shells. Do not claim to repair
    # these or allow a higher intersection-pair count than their original CAD.
    source_intersections = len(original.get_self_intersecting_triangles())
    physics_intersections = len(candidate.get_self_intersecting_triangles())
    if physics_intersections > source_intersections:
        raise ValueError('More intersecting triangle pairs than the source CAD')

    hull_before = convex_mesh(before)
    hull_after = convex_mesh(after)
    if not hull_after.is_watertight():
        raise ValueError('Invalid convex collision envelope')
    collision_error = surface_error(hull_before, hull_after)
    detail_error = surface_error(original, candidate)
    bounds_error = float(np.abs(after.bounds - before.bounds).max())
    centre_error = float(np.linalg.norm(after.center_mass - before.center_mass))
    volume_error = abs(after.volume / before.volume - 1)
    inertia_error = np.linalg.norm(after.moment_inertia - before.moment_inertia)
    inertia_error /= np.linalg.norm(before.moment_inertia)
    specific_before = before.moment_inertia / before.mass
    specific_after = after.moment_inertia / after.mass
    specific_error = np.linalg.norm(specific_after - specific_before)
    specific_error /= np.linalg.norm(specific_before)
    if max(collision_error, bounds_error, centre_error) > 0.0005:
        raise ValueError('Collision envelope, bounds or centre deviate by more than 0.5 mm')
    if detail_error > 0.002:
        raise ValueError('Physical surface detail deviates by more than 2 mm')
    if volume_error > 0.01 or max(inertia_error, specific_error) > 0.02:
        raise ValueError('Volume error exceeds 1% or inertia error exceeds 2%')
    if not np.isfinite(after.moment_inertia).all():
        raise ValueError('Non-finite inertia tensor')
    if np.linalg.eigvalsh(after.moment_inertia).min() <= 0:
        raise ValueError('Inertia tensor is not positive definite')
    return {
        'source_triangles_after_cleanup': len(original.triangles),
        'physics_triangles': len(candidate.triangles),
        'physics_vertices': len(candidate.vertices),
        'sampled_collision_envelope_error_mm': round(collision_error * 1000, 6),
        'sampled_physical_surface_error_mm': round(detail_error * 1000, 6),
        'bounds_error_mm': round(bounds_error * 1000, 6),
        'centre_of_mass_error_mm': round(centre_error * 1000, 6),
        'volume_error_percent': round(float(volume_error) * 100, 6),
        'inertia_at_fixed_density_error_percent': round(float(inertia_error) * 100, 6),
        'inertia_per_mass_error_percent': round(float(specific_error) * 100, 6),
        'source_self_intersection_pairs': source_intersections,
        'physics_self_intersection_pairs': physics_intersections,
        'physics_non_manifold_edges': non_manifold_edges,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate without writing files')
    args = parser.parse_args()
    results = {}
    for source, output, target in PARTS:
        original = load_mesh(DATA / source)
        destination = OUTPUT / output
        if args.check:
            candidate = load_mesh(destination)
        else:
            working = o3d.geometry.TriangleMesh(original)
            working.scale(1000, center=(0, 0, 0))
            candidate = working.simplify_quadric_decimation(target)
            candidate.scale(0.001, center=(0, 0, 0))
            candidate.vertices = o3d.utility.Vector3dVector(
                np.asarray(candidate.vertices).astype(np.float32).astype(np.float64),
            )
            candidate.remove_duplicated_vertices()
            candidate.remove_degenerate_triangles()
            candidate.remove_duplicated_triangles()
            validate(original, candidate, target)
            OUTPUT.mkdir(parents=True, exist_ok=True)
            write_obj(destination, candidate, source)
            candidate = load_mesh(destination)
        result = validate(original, candidate, target)
        result['source'] = source
        # Keep the raw count visible: one source has two degenerate triangles.
        result['source_triangles'] = sum(
            len(line.split()) - 3 for line in (DATA / source).read_text().splitlines()
            if line.startswith('f ')
        )
        results[output] = result
    if not args.check:
        (OUTPUT / 'validation.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
