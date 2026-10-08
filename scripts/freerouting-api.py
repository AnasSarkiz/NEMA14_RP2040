"""Route with official Freerouting 2.0.1 and explicitly serialize its SES.

An intermediate fixed-geometry CLI run produced empty output; final CLI smoke
checks can succeed. This API path retains the exact official engine and writer,
with serialization asserted independently of routing-loop completion. Physical
connectivity validation, not the loop return value, decides acceptance.
"""
import jpype,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
jpype.startJVM('-Djava.awt.headless=true',classpath=['/workspace/freerouting-2.0.1.jar']);J=jpype.JClass
job=J('app.freerouting.core.RoutingJob')();m=J('app.freerouting.interactive.HeadlessBoardManager')(J('java.util.Locale').ENGLISH,job)
s=J('java.io.FileInputStream')(str(ROOT/'artifacts/supplier-input.dsn'))
assert str(m.loadFromSpecctraDsn(s,None,J('app.freerouting.board.ItemIdentificationNumberGenerator')()))=='OK'
job.board=m.get_routing_board();job.routerSettings=J('app.freerouting.settings.RouterSettings')(job.board)
job.routerSettings.set_stop_pass_no(40);job.routerSettings.setRunOptimizer(False)
job.thread=J('app.freerouting.management.RoutingJobSchedulerActionThread')(job)
print('Loaded source-native DSN; official BatchAutorouter.runBatchLoop',flush=True)
r=J('app.freerouting.autoroute.BatchAutorouter')(job);print(r.runBatchLoop(),flush=True)
f=J('java.io.FileOutputStream')(str(ROOT/'artifacts/supplier-board.ses'))
try:assert m.saveAsSpecctraSessionSes(f,'supplier-input.dsn')
finally:f.close()
print('Explicit official SpecctraSesFileWriter succeeded',flush=True)
