"""Owned, disposable browser-test fixture; never connects to deployment storage."""
from pathlib import Path
import os
import tempfile
import uvicorn
from vaeil.adapters.persistence import open_repository


def main():
    with tempfile.TemporaryDirectory(prefix="vaeil-browser-") as directory:
        url = "sqlite:///" + (Path(directory) / "browser.sqlite").as_posix()
        os.environ["DATABASE_URL"] = url
        os.environ["VAEIL_SECURE_COOKIES"] = "0"
        os.environ.pop("VAEIL_ADMIN_EMAIL", None)
        os.environ.pop("VAEIL_ADMIN_PASSWORD", None)
        os.environ['VAEIL_ADMIN_EMAIL'] = 'browser.admin@example.invalid'
        os.environ['VAEIL_ADMIN_PASSWORD'] = 'Fictional admin password'
        os.environ['VAEIL_ENV'] = 'demo'
        os.environ['VAEIL_DEMO_LLM_FAILURE'] = '0'
        with open_repository(url) as repository:
            with repository.transaction() as unit:
                unit.issue_invite("browser-invite", issuer_id="fictional-browser-admin")
                for index in range(40):
                    unit.issue_invite(f"h1-invite-{index}", issuer_id="fictional-browser-admin")
                unit.commit()
        from datetime import date
        from vaeil.application.admission import AdmissionApplication, ApplicationSubmission, SessionPrincipal
        from vaeil.adapters import authentication
        from vaeil.domain import MemberIdentity
        from vaeil.domain.authentication import Role, AdmissionStatus, AdmissionDecision
        from vaeil.domain.profile import ProfileDraftInput
        from vaeil.domain.conversation import Conversation
        from vaeil.runtime import RuntimeClock, RuntimeTokens, HumanReviewModel
        with open_repository(url) as repository:
            admission = AdmissionApplication(repository, passwords=authentication, tokens=RuntimeTokens(),
                                             clock=RuntimeClock(), model=HumanReviewModel())
            admission.seed_admin(email='browser.admin@example.invalid', password='Fictional admin password')
            admin = SessionPrincipal('admin', Role.ADMIN, AdmissionStatus.APPROVED)
            for identifier, legal_name, pseudonym in [('browser-a', 'FictionalSun', 'Sunbeam'), ('browser-b', 'FictionalMoon', 'Moonrise'), ('reveal-a', 'FictionalRiver', 'River'), ('reveal-b', 'FictionalMeadow', 'Meadow'), ('matching-a', 'FictionalGrove', 'Horizon'), ('matching-b', 'FictionalOrchard', 'Watchtower')]:
                code = 'invite-' + identifier
                with repository.transaction() as unit:
                    unit.issue_invite(code, issuer_id='admin')
                    unit.commit()
                identity = MemberIdentity(identifier, legal_name, identifier + '@example.invalid', None, date(2000, 1, 1))
                admission.apply(ApplicationSubmission(identity, code, 'I seek a thoughtful long term relationship.',
                    authentication.hash_password('Fictional chat password')))
                admission.decide_admission(actor=admin, applicant_id=identifier, decision=AdmissionDecision.APPROVE)
                actor = SessionPrincipal(identifier, Role.MEMBER, AdmissionStatus.APPROVED)
                admission.save_own_profile(actor=actor, draft=ProfileDraftInput(pseudonym=pseudonym,
                    relationship_intent='long_term', life_stage='undergraduate', interests=['reading'], values=['honesty'],
                    communication_style='direct', pace_and_lifestyle='quiet_and_routine',
                    about='<b>Quiet afternoons.</b>' if identifier == 'matching-b' else ''))
            with repository.transaction() as unit:
                unit.store_conversation(Conversation('browser-conversation', ('browser-a', 'browser-b')))
                unit.commit()
        from datetime import timedelta
        from uuid import UUID
        from vaeil.domain.messaging import MessageRecord, assess_message
        from vaeil.domain.vetting import Verdict
        with open_repository(url) as repository:
            with repository.transaction() as unit:
                conversation = Conversation('reveal-conversation', ('reveal-a', 'reveal-b'))
                unit.store_conversation(conversation)
                first_delivery = RuntimeClock().now() - timedelta(hours=73)
                for index in range(20):
                    sender = 'reveal-a' if index < 15 else 'reveal-b'
                    text = 'A fictional delivered conversation.'
                    assessment = assess_message(text, sender_id=sender, conversation=conversation, moderation=Verdict.APPROVED)
                    unit.add_message(MessageRecord('reveal-seed-' + str(index), conversation.conversation_id, sender, text,
                        str(UUID(int=index+500)), assessment, first_delivery, delivered_at=first_delivery))
                unit.commit()
        uvicorn.run("vaeil.web:create_app", factory=True, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
