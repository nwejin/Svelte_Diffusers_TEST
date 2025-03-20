<script lang="ts">
  import { onMount } from "svelte";
  import { UserRoundPlus } from "lucide-svelte";

  // 전체 옵션 (UI는 한글, 값은 영어)
  const genderOptions = [
    { label: "남성", value: "boy" },
    { label: "여성", value: "girl" },
  ];

  const themeOptions = [
    { label: "중세 판타지", value: "medieval fantasy" },
    { label: "동양", value: "eastern" },
    { label: "미래", value: "futuristic" },
    { label: "신화", value: "mythological" },
    { label: "현대", value: "modern" },
  ];

  const familyOptions = [
    { label: "있음", value: "has family" },
    { label: "없음", value: "no family" },
  ];

  const familyHistoryOptions = [
    { label: "신생가문", value: "new family" },
    { label: "유망가문", value: "promising family" },
    { label: "명문가문", value: "noble family" },
    { label: "전설적인 가문", value: "legendary family" },
  ];

  const regionOptions = [
    { label: "도시", value: "urban" },
    { label: "시골", value: "rural" },
  ];

  const ageOptions = [
    { label: "청년 (20~40)", value: "young adult (20-40)" },
    { label: "중년 (40~60)", value: "middle-aged (40-60)" },
    { label: "노년 (60~100)", value: "elderly (60-100)" },
  ];

  const bodyTypeOptions = [
    { label: "근육형", value: "muscular" },
    { label: "날씬", value: "slim" },
    { label: "비만", value: "overweight" },
    { label: "왜소", value: "petite" },
  ];

  const clothingOptions = [
    { label: "노출 X", value: "modest clothing" },
    { label: "부분 노출", value: "partially revealing clothing" },
    { label: "과감한 노출", value: "revealing clothing" },
  ];

  const classOptions = [
    { label: "전사", value: "warrior" },
    { label: "기사", value: "knight" },
    { label: "도적", value: "thief" },
    { label: "궁수", value: "archer" },
    { label: "마법사", value: "wizard" },
  ];

  const personalityOptions = [
    { label: "ENFP", value: "ENFP" },
    { label: "ISTJ", value: "ISTJ" },
    { label: "ESTJ", value: "ESTJ" },
    { label: "INFP", value: "INFP" },
  ];

  // 선택 옵션 (값은 영어로 저장)
  let selectedGender = "boy";
  let selectedTheme = "medieval fantasy";
  let selectedFamily = "has family";
  let selectedFamilyHistory = "promising family";
  let selectedRegion = "urban";
  let selectedAge = "young adult (20-40)";
  let selectedBodyType = "slim";
  let selectedClothing = "modest clothing";
  let selectedClass = "knight";
  let selectedPersonality = "ENFP";

  // 생성 관련
  let isLoading = false;
  let generatedImage: string | null = null;
  let errorMessage: string | null = null;

  function generatePrompt(): string {
    return `anime, gray background, solo, masterpiece, best quality, amazing quality, full body shot, standing, 
    1${selectedGender}, ${selectedTheme}, 
    family: ${selectedFamily}, family history: ${selectedFamilyHistory}, 
    region: ${selectedRegion}, age: ${selectedAge}, 
    body type: ${selectedBodyType}, clothing: ${selectedClothing}, 
    class: ${selectedClass}, personality: ${selectedPersonality}`;
  }

  async function generateImage() {
    isLoading = true;
    generatedImage = null;
    errorMessage = null;

    try {
      const payload = {
        prompt: generatePrompt(),
        negative_prompt:
          "((bad hands:1)), ((extra fingers:1)), ((deformed hands:1)), ((unhealthy hands:1)), ((excess limbs:1.1)),((lowres)),((worst quality)), ((bad quality)), ((low quality)), naked, nsfw",
        num_inference_steps: 20,
        width: 512,
        height: 512,
        guidance_scale: 7,
      };

      console.log("Sending request with payload:", payload);

      const response = await fetch("http://127.0.0.1:7861/sdapi/v1/txt2img", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(
          `API 요청 실패: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();

      if (data.images && data.images.length > 0) {
        console.log("이미지 생성 완료");
        // base64 이미지를 표시
        generatedImage = `data:image/png;base64,${data.images[0]}`;
      } else {
        throw new Error("이미지가 생성되지 않았습니다.");
      }
    } catch (error) {
      console.error("이미지 생성 중 오류:", error);
      errorMessage =
        error instanceof Error
          ? error.message
          : "알 수 없는 오류가 발생했습니다.";
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="grid w-full grid-cols-3 gap-4 p-4">
  <!-- 왼쪽 컬럼: 캐릭터 외형 -->
  <div class="max-h-screen p-6 overflow-auto shadow-sm bg-gray-50 rounded-2xl">
    <h2 class="mb-6 text-xl font-bold text-center text-gray-800">
      캐릭터 외형
    </h2>

    <!-- 성별 선택 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">성별</h3>
      <div class="flex flex-wrap gap-2">
        {#each genderOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedGender ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedGender = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 테마 및 세계관 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">테마 및 세계관</h3>
      <div class="flex flex-wrap gap-2">
        {#each themeOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedTheme ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedTheme = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 나이 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">나이</h3>
      <div class="flex flex-wrap gap-2">
        {#each ageOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedAge ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedAge = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 체형 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">체형</h3>
      <div class="flex flex-wrap gap-2">
        {#each bodyTypeOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedBodyType ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedBodyType = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 의상 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">의상</h3>
      <div class="flex flex-wrap gap-2">
        {#each clothingOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedClothing ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedClothing = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 직업 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">직업</h3>
      <div class="flex flex-wrap gap-2">
        {#each classOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedClass ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedClass = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <!-- 중앙 컬럼: 이미지 결과 -->
  <div class="flex flex-col items-center justify-center">
    <div class="w-full p-4 mb-4 text-center bg-gray-100 rounded-lg">
      <h2 class="mb-2 text-xl font-bold text-gray-800">캐릭터 결과</h2>
    </div>

    <div class="flex flex-col items-center justify-center flex-grow w-full">
      {#if isLoading}
        <div class="text-center">
          <p class="mb-3 text-gray-700">캐릭터를 생성하는 중입니다...</p>
          <div
            class="inline-block w-12 h-12 mt-2 border-4 border-blue-200 rounded-full border-l-blue-600 animate-spin"
          ></div>
        </div>
      {:else if !generatedImage && !errorMessage}
        <div
          class="flex items-center justify-center w-full max-w-md bg-gray-200 rounded-lg aspect-square animate-pulse"
        >
          <div class="text-gray-400 opacity-50">
            <UserRoundPlus size={100} />
          </div>
        </div>
      {:else if errorMessage}
        <div class="w-full p-4 text-red-700 rounded-lg bg-red-50">
          <p>오류 발생: {errorMessage}</p>
        </div>
      {:else if generatedImage}
        <div class="text-center">
          <img
            src={generatedImage}
            alt="생성된 캐릭터"
            class="object-contain rounded-lg shadow-lg max-w-full max-h-[70vh]"
          />
          <div class="mt-4">
            <a
              href={generatedImage}
              download="generated-character.png"
              class="inline-flex items-center px-6 py-3 font-medium text-white transition duration-200 bg-green-600 rounded-lg hover:bg-green-700"
            >
              저장하기
            </a>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <!-- 오른쪽 컬럼: 성장 배경 -->
  <div class="max-h-screen p-6 overflow-auto shadow-sm bg-gray-50 rounded-2xl">
    <h2 class="mb-6 text-xl font-bold text-center text-gray-800">성장 배경</h2>

    <!-- 가족 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">가족</h3>
      <div class="flex flex-wrap gap-2">
        {#each familyOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedFamily ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedFamily = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 가문의 역사 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">가문의 역사</h3>
      <div class="flex flex-wrap gap-2">
        {#each familyHistoryOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedFamilyHistory ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedFamilyHistory = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 출신 지역 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">출신 지역</h3>
      <div class="flex flex-wrap gap-2">
        {#each regionOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedRegion ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedRegion = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 성격 유형 -->
    <div class="mb-6">
      <h3 class="mb-2 text-lg font-semibold text-gray-700">성격 유형</h3>
      <div class="flex flex-wrap gap-2">
        {#each personalityOptions as option}
          <button
            class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedPersonality ===
            option.value
              ? 'bg-blue-500 text-white border-blue-500'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
            on:click={() => (selectedPersonality = option.value)}
          >
            {option.label}
          </button>
        {/each}
      </div>
    </div>

    <!-- 생성 버튼 -->
    <div class="pt-6 mt-auto">
      <button
        on:click={generateImage}
        disabled={isLoading}
        class="w-full px-4 py-4 text-lg font-medium text-white transition duration-200 bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? "캐릭터 생성 중..." : "캐릭터 생성하기"}
      </button>
    </div>
  </div>
</div>
