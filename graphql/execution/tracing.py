import sys
import time

PY37 = sys.version_info[0:2] >= (3, 7)


class TracingMiddleware(object):
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self, enabled):
        self.enabled = enabled
        self.resolver_stats = list()
        self.start_time = None
        self.end_time = None
        self.parsing_start_time = None
        self.parsing_end_time = None
        self.validation_start_time = None
        self.validation_end_time = None

    def start(self):
        self.start_time = self.now()

    def end(self):
        self.end_time = self.now()

    def parsing_start(self):
        self.parsing_start_time = self.now()

    def parsing_end(self):
        self.parsing_end_time = self.now()

    def validation_start(self):
        self.validation_start_time = self.now()

    def validation_end(self):
        self.validation_end_time = self.now()

    def now(self):
        if PY37:
            return time.time_ns()

        return int(time.time() * 1000000000)

    @property
    def start_time_str(self):
        return time.strftime(self.DATETIME_FORMAT, time.gmtime(self.start_time / 1000))

    @property
    def end_time_str(self):
        return time.strftime(self.DATETIME_FORMAT, time.gmtime(self.end_time / 1000))

    @property
    def duration(self):
        if not self.end_time:
            raise ValueError("Tracing has not ended yet!")

        return self.end_time - self.start_time

    @property
    def tracing_dict(self):
        result = dict(
            version=1,
            startTime=self.start_time_str,
            endTime=self.end_time_str,
            duration=self.duration,
            parsing=dict(
                startOffset=self.parsing_start_time - self.start_time,
                duration=self.parsing_end_time - self.parsing_start_time,
            ),
            execution=dict(resolvers=self.resolver_stats),
        )

        if self.validation_start_time and self.validation_end_time:
            result["validation"] = dict(
                startOffset=self.validation_start_time - self.start_time,
                duration=self.validation_end_time - self.validation_start_time,
            )

        return result

    def resolve(self, _next, root, info, *args, **kwargs):
        if not self.enabled:
            return _next(root, info, *args, **kwargs)

        start = time.time()
        try:
            return _next(root, info, *args, **kwargs)
        finally:
            end = time.time()
            elapsed_ms = (end - start) * 1000

            stat = {
                "path": info.path,
                "parentType": str(info.parent_type),
                "fieldName": info.field_name,
                "returnType": str(info.return_type),
                "startOffset": (time.time() * 1000) - self.start_time,
                "duration": elapsed_ms,
            }
            self.resolver_stats.append(stat)
