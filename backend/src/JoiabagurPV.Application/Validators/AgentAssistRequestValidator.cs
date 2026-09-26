using FluentValidation;
using JoiabagurPV.Application.Configuration;
using JoiabagurPV.Application.DTOs.Ai;
using Microsoft.Extensions.Options;

namespace JoiabagurPV.Application.Validators;

/// <summary>
/// Validator for <see cref="AgentAssistRequest"/>: the three transcript caps, checked
/// <strong>before</strong> a provider call is spent. C42.
/// </summary>
/// <remarks>
/// <para>
/// <strong>Not delegated to the AI service, and the reason is the cost of learning.</strong> The
/// service refuses an over-long transcript with a 422, which is correct — but the caller would have
/// paid the round trip to be told its request was malformed, and on this route that round trip
/// competes for a tokens-per-minute quota that admits about one request per minute. Refusing here
/// costs nothing and spares the operator a rejection they can be warned about instead.
/// </para>
/// <para>
/// <strong>The three are independent, and the total is the one that is easy to miss.</strong> It
/// sums <em>every</em> turn, the ones attributed to the assistant included, so twelve turns each
/// within the per-turn cap can still exceed it — and does, because the argument is sent back
/// verbatim at a median of 386 characters. A validator checking only the other two would pass
/// requests the service rejects, which is exactly the failure this class exists to remove.
/// </para>
/// <para>
/// <strong>And at least one operator turn</strong>, because the turn being answered is the last of
/// those: a transcript of nothing but assistant turns asks no question.
/// </para>
/// <para>
/// Messages in es-ES, as every operator-facing validation message in this system is.
/// </para>
/// </remarks>
public class AgentAssistRequestValidator : AbstractValidator<AgentAssistRequest>
{
    public AgentAssistRequestValidator(IOptionsMonitor<AiFreeQuerySearchOptions> options)
    {
        RuleFor(x => x.Turns)
            .NotEmpty()
            .WithMessage("La conversación tiene que llevar al menos un turno.")
            .Must(turns => turns.Count <= AgentTranscriptCaps.MaxTurns)
            .WithMessage(
                $"La conversación no puede pasar de {AgentTranscriptCaps.MaxTurns} turnos, "
                + "contando los del asistente.")
            // The operator's turn is the question. Without one there is nothing to answer, and the
            // service would refuse it for the same reason.
            .Must(turns => turns.Any(turn => turn.Role == AgentTranscriptCaps.OperatorRole))
            .WithMessage("La conversación tiene que llevar al menos un turno del operario.")
            // **The cap the other two do not imply.** Summed over every turn, never over the
            // operator's alone: with the argument returned in the assistant's turns, the sum is
            // what runs out first in a long conversation.
            .Must(turns => turns.Sum(turn => turn.Text?.Length ?? 0)
                           <= AgentTranscriptCaps.MaxTranscriptChars)
            .WithMessage(
                $"La conversación no puede pasar de {AgentTranscriptCaps.MaxTranscriptChars} "
                + "caracteres en total, sumando todos los turnos.");

        RuleForEach(x => x.Turns).ChildRules(turn =>
        {
            turn.RuleFor(t => t.Text)
                .NotEmpty()
                .WithMessage("Ningún turno de la conversación puede estar vacío.")
                .Must(text => (text?.Length ?? 0) <= AgentTranscriptCaps.MaxTurnChars)
                .WithMessage(
                    $"Ningún turno puede pasar de {AgentTranscriptCaps.MaxTurnChars} caracteres.");

            turn.RuleFor(t => t.Role)
                .Must(role => role is AgentTranscriptCaps.OperatorRole
                                      or AgentTranscriptCaps.AssistantRole)
                .WithMessage(
                    $"El turno tiene que ser «{AgentTranscriptCaps.OperatorRole}» o "
                    + $"«{AgentTranscriptCaps.AssistantRole}».");
        });

        // The page ceiling is the free query's, from configuration through `IOptionsMonitor`, so the
        // two sibling panels cannot end up with different limits after a configuration change.
        RuleFor(x => x.PageSize)
            .Must(size => size is null || size >= 1)
            .WithMessage("El tamaño de página debe ser al menos 1.")
            .Must(size => size is null || size <= options.CurrentValue.MaxPageSize)
            .WithMessage(_ => $"El tamaño de página no puede superar {options.CurrentValue.MaxPageSize}.");
    }
}
