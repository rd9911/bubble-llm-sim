from bubble_sim.utils.traces import TraceWriter


def test_trace_writer(tmp_path):
    trace_file = tmp_path / "traces.jsonl"
    writer = TraceWriter(trace_file)

    event1 = {"step": 1, "value": "a"}
    event2 = {"step": 2, "value": "b"}

    writer.append(event1)
    writer.append(event2)

    events = writer.read_all()
    assert len(events) == 2
    assert events[0] == event1
    assert events[1] == event2
