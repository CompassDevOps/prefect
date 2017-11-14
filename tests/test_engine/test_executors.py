import distributed
from distributed.utils_test import cluster, loop
import pytest

import prefect
import prefect.engine.executors as executors


@pytest.fixture()
def local_executor():
    return executors.LocalExecutor()


@pytest.fixture()
def distributed_executor():
    return executors.DistributedExecutor()


def test_submit_local_executor(local_executor):
    """
    Tests that functions submitted to LocalExecutor are run properly
    """

    with local_executor() as e:
        assert e.submit(lambda: 1) == 1
        assert e.submit(lambda x, y: x + y, 1, 2) == 3
        x, y = 1, 2
        assert e.submit(lambda: x + y) == 3


def test_wait_local_executor(local_executor):
    """
    Tests that the LocalExecutor wait just returns the result
    """
    with local_executor() as e:
        assert e.wait(e.submit(lambda: 1)) == 1
        assert e.wait(e.submit(lambda x, y: x + y, 1, 2)) == 3
        x, y = 1, 2
        assert e.wait(e.submit(lambda: x + y) == 3)


def test_submit_distributed_executor(client, distributed_executor):

    with distributed_executor(client=client) as e:
        r1 = e.submit(lambda: 1) == 1
        assert e.submit(lambda x, y: x + y, 1, 2) == 3
        x, y = 1, 2
        assert e.submit(lambda: x + y) == 3


def test_distributed_flowrunner(client, distributed_executor):
    with prefect.Flow('flow') as f:
        t1 = prefect.tasks.FunctionTask(fn=lambda: 1, name='t1')
        t2 = prefect.tasks.FunctionTask(fn=lambda: 2, name='t2')
        t1.run_before(t2)
    with distributed_executor(client=client) as e:
        future = e.run_flow(f)
        assert isinstance(future, distributed.Future)

        result = e.wait(future)
        assert len(result) == 3
        assert result['state'].is_successful()
        assert result['task_states']['t1'].is_successful()
        assert result['task_states']['t2'].is_successful()
        assert result['task_results']['t1'] == 1
        assert result['task_results']['t2'] == 2