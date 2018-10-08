# -*- coding=utf-8 -*-
from datetime import datetime
import pytest
import subprocess
import textwrap
from unittest.mock import Mock

import yaml

from zettarepl.definition.definition import Definition
from zettarepl.snapshot.list import list_snapshots
from zettarepl.snapshot.snapshot import Snapshot
from zettarepl.transport.local import LocalShell
from zettarepl.zettarepl import Zettarepl


@pytest.mark.parametrize("hold_pending_snapshots,remains", [
    (True, [
        Snapshot("data/src", "2018-10-01_01-00"),
        Snapshot("data/src", "2018-10-01_02-00"),
        Snapshot("data/src", "2018-10-01_03-00")
    ]),
    (False, [
        Snapshot("data/src", "2018-10-01_02-00"),
        Snapshot("data/src", "2018-10-01_03-00")
    ]),
])
def test_hold_pending_snapshots(hold_pending_snapshots, remains):
    subprocess.call("zfs destroy -r data/src", shell=True)
    subprocess.call("zfs destroy -r data/dst", shell=True)

    subprocess.check_call("zfs create data/src", shell=True)
    subprocess.check_call("zfs snapshot data/src@2018-10-01_00-00", shell=True)
    subprocess.check_call("zfs snapshot data/src@2018-10-01_01-00", shell=True)
    subprocess.check_call("zfs snapshot data/src@2018-10-01_02-00", shell=True)
    subprocess.check_call("zfs snapshot data/src@2018-10-01_03-00", shell=True)

    subprocess.check_call("zfs create data/dst", shell=True)
    subprocess.check_call("zfs snapshot data/dst@2018-10-01_00-00", shell=True)

    definition = Definition.from_data(yaml.load(textwrap.dedent("""\
        timezone: "UTC"

        periodic-snapshot-tasks:
          - id: src
            dataset: data/src
            recursive: true
            lifetime: PT1H
            naming-schema: "%Y-%m-%d_%H-%M"
            schedule:
              minute: "0"
              hour: "*"
              day-of-month: "*"
              month: "*"
              day-of-week: "*"

        replication-tasks:
          - id: src
            direction: push
            transport:
              type: local
            source-dataset: data/src
            target-dataset: data/dst
            recursive: true
            periodic-snapshot-tasks:
              - src
            auto: true
            retention-policy: source
            hold-pending-snapshots: """ + yaml.dump(hold_pending_snapshots) + """
    """)))

    local_shell = LocalShell()
    zettarepl = Zettarepl(Mock(), local_shell)
    zettarepl.set_tasks(definition.tasks)
    zettarepl._run_local_retention(datetime(2018, 10, 1, 3, 0))

    assert list_snapshots(local_shell, "data/src", False) == remains