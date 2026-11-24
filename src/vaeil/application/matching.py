"""Orchestrate Match proposals and bilateral acceptance in owned transactions."""
from dataclasses import dataclass, replace

from vaeil.application.admission import SessionPrincipal
from vaeil.domain.authentication import AccessDeniedError, AdmissionStatus, Role
from vaeil.domain.conversation import Conversation, MemberAlreadyActiveError, PairBlockedError
from vaeil.domain.matching import Match, MatchConflictError, MatchDecision, rank_pairs
from vaeil.domain.member import PreRevealMemberView
from vaeil.domain.repository import MemberNotFoundError


@dataclass(frozen=True, slots=True)
class MatchView:
    match_id: str
    state: str
    decision: MatchDecision | None
    partner: PreRevealMemberView
    conversation_id: str | None


class MatchingApplication:
    def __init__(self, repository, *, tokens):
        self.repository, self.tokens = repository, tokens

    @staticmethod
    def _require(unit, actor, role: Role):
        principal = unit.get_principal(actor.principal_id) if isinstance(actor, SessionPrincipal) else None
        if principal is None or principal.role is not role or principal.admission is not AdmissionStatus.APPROVED:
            raise AccessDeniedError("Access is not permitted.")

    def propose_matches(self, *, actor) -> int:
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.ADMIN)
            profiles = {member.identity.member_id: member.values_profile for member in unit.list_matching_members()}
            conversations = unit.list_conversations()
            matches = unit.list_matches()
            excluded = {frozenset(item.participant_ids) for item in (*conversations, *matches)}
            unavailable = {member_id for pair in conversations if pair.active for member_id in pair.participant_ids}
            unavailable.update(member_id for match in matches if match.state == "pending" for member_id in match.participant_ids)
            created = 0
            for pair in rank_pairs(profiles, excluded_pairs=excluded, unavailable_ids=unavailable):
                if unavailable.isdisjoint(pair.participant_ids):
                    unit.create_match(Match(self.tokens.new_id(), pair.participant_ids))
                    unavailable.update(pair.participant_ids)
                    created += 1
            unit.commit()
        return created

    @staticmethod
    def _view(unit, match: Match, viewer_id: str) -> MatchView:
        index = match.participant_index(viewer_id)
        partner = unit.get_member(match.participant_ids[1 - index])
        return MatchView(match.match_id, match.state, match.decisions[index],
                         PreRevealMemberView(partner.pseudonym, partner.values_profile), match.conversation_id)

    def read_matches(self, *, actor) -> tuple[MatchView, ...]:
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.MEMBER)
            return tuple(self._view(unit, match, actor.principal_id)
                         for match in unit.list_member_matches(actor.principal_id))

    def decide_match(self, *, actor, match_id: str, decision: MatchDecision) -> MatchView:
        with self.repository.transaction() as unit:
            self._require(unit, actor, Role.MEMBER)
            previous = unit.get_match(match_id)
            match = previous.record_decision(actor.principal_id, decision)
            if match is previous:
                return self._view(unit, match, actor.principal_id)
            if match.decisions == (MatchDecision.ACCEPT, MatchDecision.ACCEPT):
                try:
                    for member_id in match.participant_ids:
                        principal = unit.get_principal(member_id)
                        if principal is None or principal.role is not Role.MEMBER or principal.admission is not AdmissionStatus.APPROVED:
                            raise MatchConflictError("This Match cannot open a Conversation.")
                        unit.get_member(member_id)
                    if any(frozenset(item.participant_ids) == frozenset(match.participant_ids)
                           for item in unit.list_conversations()):
                        raise MatchConflictError("This Match cannot open a Conversation.")
                    conversation = Conversation(self.tokens.new_id(), match.participant_ids)
                    unit.store_conversation(conversation)
                except (MemberNotFoundError, MemberAlreadyActiveError, PairBlockedError):
                    raise MatchConflictError("This Match cannot open a Conversation.") from None
                match = replace(match, conversation_id=conversation.conversation_id)
            unit.update_match(match)
            view = self._view(unit, match, actor.principal_id)
            unit.commit()
            return view

