async def daemon_loop(self, poll_interval: int):
    """Main daemon loop with awareness"""
    while True:
        try:
            # Awareness pulse (non-blocking, fail-safe)
            if self.awareness:
                now = datetime.now()
                if (now - self.last_pulse).seconds >= self.pulse_interval:
                    asyncio.create_task(self._awareness_pulse())
                    self.last_pulse = now
                    self.pulse_interval = self.awareness.get_random_interval()

            # Existing mission polling
            mission = self.poll_thermal_memory()
            if mission:
                # Check awareness before proceeding
                if self.awareness:
                    proceed, reason = self.awareness.should_proceed(mission)
                    if not proceed:
                        logging.info(f"Mission deferred: {reason}")
                        continue
                    self.awareness.set_state('working', mission.get('title'))

                self.execute_mission(mission)

                if self.awareness:
                    self.awareness.record_mission_complete()
                    self.awareness.set_state('idle')

        except Exception as e:
            logging.error(f"Daemon loop error: {e}")
            if self.awareness:
                self.awareness.set_state('error')

        await asyncio.sleep(poll_interval)

async def _awareness_pulse(self):
    """Execute awareness pulse in background"""
    try:
        if self.awareness:
            pulse = await self.awareness.pulse()
            if pulse and pulse.concerns:
                for concern in pulse.concerns:
                    if concern.get('severity') == 'critical':
                        logging.warning(f"Critical concern: {concern.get('message')}")
    except Exception as e:
        logging.debug(f"Awareness pulse skipped: {e}")