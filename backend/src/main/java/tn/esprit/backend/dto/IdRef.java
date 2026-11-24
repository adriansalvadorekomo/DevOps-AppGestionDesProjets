package tn.esprit.backend.dto;

/** A reference to another record by id only, e.g. {"entreprise": {"id": 2}}. */
public record IdRef(Long id) {
}
