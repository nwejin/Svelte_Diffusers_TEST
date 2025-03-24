export interface OptionItem {
	label: string;
	value: string;
}

export interface PromptOptions {
	genderOptions: OptionItem[];
	themeOptions: OptionItem[];
	familyOptions: OptionItem[];
	familyHistoryOptions: OptionItem[];
	regionOptions: OptionItem[];
	ageOptions: OptionItem[];
	bodyTypeOptions: OptionItem[];
	clothingOptions: OptionItem[];
	classOptions: OptionItem[];
	personalityOptions: OptionItem[];
}

export const promptOptions: PromptOptions = {
	genderOptions: [
		{ label: "남성", value: "boy" },
		{ label: "여성", value: "girl" },
	],

	themeOptions: [
		{ label: "중세 판타지", value: "medieval fantasy" },
		{ label: "동양", value: "eastern" },
		{ label: "미래", value: "futuristic" },
		{ label: "신화", value: "mythological" },
		{ label: "현대", value: "modern" },
	],

	familyOptions: [
		{ label: "있음", value: "has family" },
		{ label: "없음", value: "no family" },
	],

	familyHistoryOptions: [
		{ label: "신생가문", value: "new family" },
		{ label: "유망가문", value: "promising family" },
		{ label: "명문가문", value: "noble family" },
		{ label: "전설적인 가문", value: "legendary family" },
	],

	regionOptions: [
		{ label: "도시", value: "urban" },
		{ label: "시골", value: "rural" },
	],

	ageOptions: [
		{ label: "청년 (20~40)", value: "young adult (20-40)" },
		{ label: "중년 (40~60)", value: "middle-aged (40-60)" },
		{ label: "노년 (60~100)", value: "elderly (60-100)" },
	],

	bodyTypeOptions: [
		{ label: "근육형", value: "muscular" },
		{ label: "날씬", value: "slim" },
		{ label: "비만", value: "overweight" },
		{ label: "왜소", value: "petite" },
	],

	clothingOptions: [
		{ label: "노출 X", value: "modest clothing" },
		{ label: "부분 노출", value: "partially revealing clothing" },
		{ label: "과감한 노출", value: "revealing clothing" },
	],

	classOptions: [
		{ label: "전사", value: "warrior" },
		{ label: "기사", value: "knight" },
		{ label: "도적", value: "thief" },
		{ label: "궁수", value: "archer" },
		{ label: "마법사", value: "wizard" },
	],

	personalityOptions: [
		{ label: "ENFP", value: "ENFP" },
		{ label: "ISTJ", value: "ISTJ" },
		{ label: "ESTJ", value: "ESTJ" },
		{ label: "INFP", value: "INFP" },
	],
};

export const defaultSelections = {
	selectedGender: "boy",
	selectedTheme: "medieval fantasy",
	selectedFamily: "has family",
	selectedFamilyHistory: "promising family",
	selectedRegion: "urban",
	selectedAge: "young adult (20-40)",
	selectedBodyType: "slim",
	selectedClothing: "modest clothing",
	selectedClass: "knight",
	selectedPersonality: "ENFP",
};
