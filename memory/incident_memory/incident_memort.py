class IncidentMemory:

    def __init__(self):
        self.storage = []

    def save_incident(self, incident):
        self.storage.append(incident)

    def list_incidents(self):
        return self.storage
