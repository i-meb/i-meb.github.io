```{=html}
<ul class="presentation-list list">
<% for (const item of items) { %>
  <li class="presentation-item" <%= metadataAttrs(item) %>>
    <div class="presentation-meta"><span class="listing-year"><%= item.year %></span> · <span class="listing-type"><%= item.type %></span></div>
    <div class="presentation-title listing-title"><%= item.title %></div>
    <div class="presentation-meta"><span class="listing-event"><%= item.event %></span><% if (item.location) { %> · <%= item.location %><% } %></div>
    <% if (item.url) { %><div class="presentation-links"><a href="<%- item.url %>" target="_blank" rel="noopener">Link</a></div><% } %>
  </li>
<% } %>
</ul>
```
