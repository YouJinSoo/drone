let map;
let markers = [];

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 37.5665, lng: 126.9780 }, // 서울 시청 기준
    zoom: 12,
  });
}

// 마커 렌더링 함수
function renderMarkers(persons) {
  clearMarkers();

  persons.forEach(person => {
    const marker = new google.maps.Marker({
      position: { lat: person.lat, lng: person.lng },
      map: map,
      title: person.name,
    });

    marker.addListener("click", () => {
      showDetail(person);
      map.panTo(marker.getPosition());
      map.setZoom(15);
    });

    markers.push(marker);
  });
}

// 검색 결과 리스트 렌더링 함수
function renderResultList(persons) {
  const resultList = document.getElementById("resultList");
  resultList.innerHTML = "";

  if (persons.length === 0) {
    resultList.innerHTML = "<p>검색 결과가 없습니다.</p>";
    document.getElementById("missingImage").src = "";
    document.getElementById("missingInfo").textContent = "검색 결과를 클릭하세요.";
    return;
  }

  persons.forEach(person => {
    const div = document.createElement("div");
    div.className = "result-item";
    div.innerHTML = `
      <img src="${person.img}" alt="${person.name}" />
      <div>
        <p>${person.name}</p>
        <p>상의: ${person.topColor}, 하의: ${person.bottomColor}</p>
      </div>
    `;

    div.addEventListener("click", () => {
      showDetail(person);
      map.panTo({lat: person.lat, lng: person.lng});
      map.setZoom(15);
    });

    resultList.appendChild(div);
  });
}

// 상세정보 보여주기
function showDetail(person) {
  document.getElementById("missingImage").src = person.img;
  document.getElementById("missingInfo").textContent = `${person.name} / 상의: ${person.topColor} / 하의: ${person.bottomColor}`;
}

// 마커 모두 제거
function clearMarkers() {
  markers.forEach(marker => marker.setMap(null));
  markers = [];
}

// 검색 시작 버튼 이벤트
document.getElementById("searchBtn").addEventListener("click", () => {
  const topColor = document.getElementById("topColor").value;
  const bottomColor = document.getElementById("bottomColor").value;

  fetch("/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ topColor, bottomColor })
  })
  .then(response => response.json())
  .then(data => {
    // 서버에서 { persons: [...] } 형태로 응답한다고 가정
    renderMarkers(data.persons);
    renderResultList(data.persons);
  })
  .catch(err => {
    console.error(err);
    alert("서버에서 데이터를 받아오지 못했습니다.");
  });
});

// 구글맵 콜백으로 initMap 등록
window.initMap = initMap;