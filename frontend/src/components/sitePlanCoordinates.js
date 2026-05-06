export const PLAN_WIDTH = 1018;
export const PLAN_HEIGHT = 880;
export const PLAN_BOUNDS = [
  [0, 0],
  [PLAN_HEIGHT, PLAN_WIDTH],
];

// Emplacements capteurs (zones) recales visuellement sur le plan du site.
export const ZONE_PLAN_POINTS = {
  1: { x: 240, y: 400 },
  2: { x: 300, y: 430 },
  3: { x: 360, y: 450 },
  4: { x: 430, y: 455 },
  5: { x: 500, y: 455 },
  6: { x: 565, y: 455 },
  7: { x: 460, y: 560 },
  8: { x: 555, y: 560 },
  9: { x: 650, y: 485 },
  10: { x: 705, y: 455 },
  11: { x: 760, y: 430 },
  12: { x: 640, y: 640 },
  13: { x: 280, y: 700 },
};

// Emplacements compteurs recales sur les zones baties du plan central.
export const METER_PLAN_POINTS = {
  AMPERE_1: { x: 620, y: 460 },
  AMPERE_2: { x: 640, y: 500 },
  BCA1: { x: 390, y: 470 },
  BCA2: { x: 410, y: 500 },
  BECQUEREL: { x: 350, y: 530 },
  CCAS: { x: 300, y: 690 },
  CHARPAK: { x: 720, y: 500 },
  EINSTEIN: { x: 680, y: 445 },
  SIMULATEUR: { x: 265, y: 725 },
  FARADAY: { x: 560, y: 470 },
  FRANKLIN: { x: 740, y: 420 },
  JOLIOT_CURIE_1: { x: 485, y: 445 },
  JOLIOT_CURIE_2: { x: 515, y: 445 },
  NEWTON: { x: 800, y: 530 },
  PAP: { x: 700, y: 620 },
  VOLTA: { x: 770, y: 675 },
  AVOGADRO: { x: 230, y: 520 },
  EDISON: { x: 210, y: 650 },
  COULOMB1: { x: 450, y: 690 },
  COULOMB2: { x: 530, y: 690 },
  TREMPLIN: { x: 620, y: 690 },
  SALLE_MUSCULATION: { x: 340, y: 700 },
};
