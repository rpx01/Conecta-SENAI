def test_forgot_post_sends_email_async(client, csrf_token, monkeypatch):
    called = {}

    def fake_send(msg):
        called['called'] = True

    class DummyThread:
        def __init__(self, target, args=(), daemon=None):
            self.target = target
            self.args = args
            self.daemon = daemon

        def start(self):
            # execute synchronously to keep test deterministic
            self.target(*self.args)

    monkeypatch.setattr('src.blueprints.auth_reset.mail.send', fake_send)
    monkeypatch.setattr('src.blueprints.auth_reset.Thread', DummyThread)

    response = client.post('/forgot', data={'email': 'admin@example.com', 'csrf_token': csrf_token})
    assert response.status_code == 302
    # ensure our fake send was called
    assert called.get('called') is True
