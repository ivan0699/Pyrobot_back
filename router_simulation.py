# global imports
from fastapi import APIRouter, Depends, status, HTTPException

# local imports
from authentication import get_current_user_name
from models import SimulationModel, RobotToUserModel
from game import Game

router = APIRouter(prefix='/simulation')


@router.post('/create')
async def simulation_create(
        simulation: SimulationModel,
        current_user: str = Depends(get_current_user_name)):
    rounds, robots_names = simulation.dict().values()

    # check if simulation has valid number of robots
    if len(robots_names) > 4:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Too many robots'
        )

    if len(robots_names) < 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='No robots to simulate'
        )

    if len(robots_names) == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Add at least one more robot'
        )

    # check if simulation has valid number of rounds
    if rounds < 1 or rounds > 10000:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Rounds must be between 1 and 10000'
        )

    robots_for_simulation = [RobotToUserModel(name=r, owner_name=current_user)
                             for r in robots_names]

    game = Game(simulation.rounds, 1, robots_for_simulation, True)
    results = game.play()
    return results
