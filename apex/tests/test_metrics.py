from apex_stream.metrics import StreamMetrics


def test_snapshot_reports_active_streams_and_average_timings():
    metrics = StreamMetrics()
    metrics.stream_started()
    metrics.observe_timing("startup", 0.1)
    metrics.observe_timing("startup", 0.3)
    metrics.observe_timing("operation", 1.0)
    metrics.record_stream({"duration": 3.0, "bytes_sent": 10})

    snapshot = metrics.snapshot()
    assert snapshot["active_streams"] == 1
    assert snapshot["average_startup_seconds"] == 0.2
    assert snapshot["average_operation_seconds"] == 2.0
    assert snapshot["timings"]["startup"]["count"] == 2

    metrics.stream_finished()
    assert metrics.snapshot()["active_streams"] == 0
