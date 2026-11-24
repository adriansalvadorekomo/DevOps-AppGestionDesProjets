package tn.esprit.backend.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

/** Client mistakes are 4xx answers, never a NullPointerException or a 500. */
public final class ApiErrors {

    private ApiErrors() {
    }

    public static ResponseStatusException notFound(String entity, Long id) {
        return new ResponseStatusException(HttpStatus.NOT_FOUND, entity + " " + id + " not found");
    }

    public static ResponseStatusException idRequired() {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, "id is required to update");
    }
}
