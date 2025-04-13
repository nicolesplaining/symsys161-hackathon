import scipy.sparse.linalg as spla
import scipy.sparse.linalg.dsolve as dsolve

dsolve.use_solver(useUmfpack=False)

from dl4to.datasets import SELTODataset
from dl4to.criteria import Compliance, VolumeConstraint
from dl4to.topo_solvers import SIMP
from dl4to.pde import FDM

def load_data(name='disc_complex', idx=0, pde=FDM(padding_depth=0)):
  dataset = SELTODataset("../dl4to_dataset", name=name)
  problem, gt_solution = dataset[idx]
  
  problem.pde_solver = pde
  return problem, gt_solution

def simp_solve(problem, criterion, iters=10, lr=5e-1):
  simp = SIMP(
    criterion=criterion,
    binarizer_steepening_factor=1.02,
    n_iterations=iters,
    lr=lr,
  )

  solution = simp(problem)
  return solution

def viz(to_viz):
  camera_position = (0, 0.06, 0.12)
  for item in to_viz:
    item.plot(camera_position=camera_position,
              use_pyvista=True,
              smooth_iters=100,
              window_size=(600,600),
              display=True)

def main():
  problem, gt_solution = load_data()

  criterion = Compliance() + VolumeConstraint(max_volume_fraction=0.12, threshold_fct='relu')

  solution = simp_solve(problem, criterion)

  viz([problem, solution]) 

main()