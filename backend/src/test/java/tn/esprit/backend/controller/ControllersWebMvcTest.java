package tn.esprit.backend.controller;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatchers;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import tn.esprit.backend.entity.Entreprise;
import tn.esprit.backend.entity.Equipe;
import tn.esprit.backend.entity.Projet;
import tn.esprit.backend.entity.ProjetDetaille;
import tn.esprit.backend.service.IEntrepriseService;
import tn.esprit.backend.service.IEquipeService;
import tn.esprit.backend.service.IProjetDetailleService;
import tn.esprit.backend.service.IProjetService;

/** HTTP contract of the four REST controllers (service layer mocked). */
@WebMvcTest({ProjetController.class, EntrepriseController.class, EquipeController.class, ProjetDetailleController.class})
class ControllersWebMvcTest {

    @Autowired MockMvc mvc;
    @MockitoBean IProjetService projetService;
    @MockitoBean IEntrepriseService entrepriseService;
    @MockitoBean IEquipeService equipeService;
    @MockitoBean IProjetDetailleService projetDetailleService;

    @Test
    void projetEndpoints() throws Exception {
        Projet p = Projet.builder().id(1L).sujet("ERP").build();
        when(projetService.getAllProjets()).thenReturn(List.of(p));
        when(projetService.getProjetById(1L)).thenReturn(p);
        when(projetService.addProjet(ArgumentMatchers.any(Projet.class))).thenReturn(p);
        mvc.perform(get("/projet/all")).andExpect(status().isOk()).andExpect(jsonPath("$[0].sujet").value("ERP"));
        mvc.perform(get("/projet/get/1")).andExpect(status().isOk()).andExpect(jsonPath("$.id").value(1));
        mvc.perform(post("/projet/add").contentType(MediaType.APPLICATION_JSON).content("{\"sujet\":\"ERP\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.sujet").value("ERP"));
        mvc.perform(delete("/projet/delete/1")).andExpect(status().isOk());
        verify(projetService).deleteProjet(1L);
    }

    @Test
    void entrepriseEndpoints() throws Exception {
        Entreprise e = Entreprise.builder().id(2L).nom("Acme").adresse("Tunis").build();
        when(entrepriseService.getAllEntreprises()).thenReturn(List.of(e));
        when(entrepriseService.updateEntreprise(ArgumentMatchers.any(Entreprise.class))).thenReturn(e);
        mvc.perform(get("/entreprise/all")).andExpect(status().isOk()).andExpect(jsonPath("$[0].nom").value("Acme"));
        mvc.perform(put("/entreprise/update").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"id\":2,\"nom\":\"Acme\",\"adresse\":\"Tunis\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.adresse").value("Tunis"));
    }

    @Test
    void equipeAssignmentEndpoints() throws Exception {
        Equipe q = Equipe.builder().id(3L).nom("Data").specialite("ETL").build();
        when(equipeService.getEquipesByEntreprise(2L)).thenReturn(List.of(q));
        when(equipeService.assignEquipeToEntreprise(3L, 2L)).thenReturn(q);
        mvc.perform(get("/equipe/by-entreprise/2")).andExpect(status().isOk()).andExpect(jsonPath("$[0].nom").value("Data"));
        mvc.perform(put("/equipe/assign-entreprise/3/2")).andExpect(status().isOk()).andExpect(jsonPath("$.id").value(3));
    }

    @Test
    void projetDetailleEndpoints() throws Exception {
        ProjetDetaille d = ProjetDetaille.builder().id(4L).technologie("Angular").coutProvisoire(5000.0).build();
        when(projetDetailleService.getProjetDetaillesByProjet(1L)).thenReturn(List.of(d));
        when(projetDetailleService.assignProjetDetailleToProjet(4L, 1L)).thenReturn(d);
        mvc.perform(get("/projet-detaille/by-projet/1")).andExpect(status().isOk())
                .andExpect(jsonPath("$[0].technologie").value("Angular"));
        mvc.perform(put("/projet-detaille/assign-projet/4/1")).andExpect(status().isOk())
                .andExpect(jsonPath("$.coutProvisoire").value(5000.0));
    }

    @Test
    void remainingCrudRoutesReachTheirService() throws Exception {
        String json = "{\"id\":1}";
        mvc.perform(put("/projet/update").contentType(MediaType.APPLICATION_JSON).content(json)).andExpect(status().isOk());
        verify(projetService).updateProjet(ArgumentMatchers.any(Projet.class));

        mvc.perform(post("/entreprise/add").contentType(MediaType.APPLICATION_JSON).content(json)).andExpect(status().isOk());
        mvc.perform(get("/entreprise/get/1")).andExpect(status().isOk());
        mvc.perform(delete("/entreprise/delete/1")).andExpect(status().isOk());
        verify(entrepriseService).addEntreprise(ArgumentMatchers.any(Entreprise.class));
        verify(entrepriseService).getEntrepriseById(1L);
        verify(entrepriseService).deleteEntreprise(1L);

        mvc.perform(post("/equipe/add").contentType(MediaType.APPLICATION_JSON).content(json)).andExpect(status().isOk());
        mvc.perform(put("/equipe/update").contentType(MediaType.APPLICATION_JSON).content(json)).andExpect(status().isOk());
        mvc.perform(get("/equipe/get/1")).andExpect(status().isOk());
        mvc.perform(get("/equipe/all")).andExpect(status().isOk());
        mvc.perform(put("/equipe/assign-projet/1/2")).andExpect(status().isOk());
        mvc.perform(delete("/equipe/delete/1")).andExpect(status().isOk());
        verify(equipeService).assignEquipeToProjet(1L, 2L);
        verify(equipeService).deleteEquipe(1L);

        mvc.perform(post("/projet-detaille/add").contentType(MediaType.APPLICATION_JSON).content(json)).andExpect(status().isOk());
        mvc.perform(put("/projet-detaille/update").contentType(MediaType.APPLICATION_JSON).content(json)).andExpect(status().isOk());
        mvc.perform(get("/projet-detaille/get/1")).andExpect(status().isOk());
        mvc.perform(get("/projet-detaille/all")).andExpect(status().isOk());
        mvc.perform(delete("/projet-detaille/delete/1")).andExpect(status().isOk());
        verify(projetDetailleService).getAllProjetsDetailles();
        verify(projetDetailleService).deleteProjetDetaille(1L);
    }
}
