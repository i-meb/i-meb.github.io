```{=html}
<ul class="pub-list list">
<% for (const item of items) { %>
  <li class="pub-item" <%= metadataAttrs(item) %>>
    <div class="pub-meta"><span class="listing-year"><%= item.year %></span> · <span class="listing-type"><%= item.type %></span><% if (item.status) { %> · <span class="badge-soft"><%= item.status %></span><% } %></div>
    <div class="pub-title listing-title"><%= item.title %></div>
    <% if (item.authors) { %><div class="pub-authors"><%= item.authors %></div><% } %>
    <% if (item.venue) { %><div class="pub-venue"><%= item.venue %></div><% } %>
    <div class="pub-links">
      <% if (item.doi_url) { %><a href="<%- item.doi_url %>" target="_blank" rel="noopener">DOI</a><% } %>
      <% if (item.url && item.url !== item.doi_url) { %><a href="<%- item.url %>" target="_blank" rel="noopener">Link</a><% } %>
      <% if (item.orcid_url) { %><a href="<%- item.orcid_url %>" target="_blank" rel="noopener">ORCID</a><% } %>
    </div>
  </li>
<% } %>
</ul>
```
