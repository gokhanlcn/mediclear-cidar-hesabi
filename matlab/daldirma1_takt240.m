%% MediClear – 1. daldırma istasyonu (İst. 4): 240 s takt için U1 ve T_m0 iterasyonu
% Süzülme (çekmeden sonra filmin akması) İPTAL: film çekme anındaki kalınlığını korur, h = h_0.
%
% Adım 1 – U1 iterasyonu (istasyon süresi = takt):
%   t_ist(U1) = t_indeks + t_iniş + t_batır + t_bekleme + L/U1 + t_damla + t_kalkış
%   f(U1) = t_ist(U1) − takt = 0  ->  ikiye bölme (bisection)
% Adım 2 – T_m0 iterasyonu (kalınlık = hedef):
%   s_1 = (1 − ε)·(s_jel(T_m0) + h_0(U1)) = s_hedef  ->  ikiye bölme
% Adım 3 – Ön ısıtma: banyoya T_m0 ile girmek için gereken fırın sıcaklığı (D1, tersine),
%   t_ön = takt − t_indeks, taşımada havada soğuma dahil.
%
% Model (hesaplayıcı programla aynı denklemler):
%   D1  ön ısıtma (toplu kütle) + taşımada havada soğuma
%   D3  jel katmanı: silindirik 1B geçici ısı iletimi (sonlu hacim, Crank–Nicolson)
%   D5  Arrhenius viskozite
%   D7  film: R_s > ℓ_c ise min(D7a, D7c), değilse D7b
%   D9  s_kür = (1 − ε)(s_jel + h_0)

clear; clc;

%% 1) Girdiler (SI birimleri)
% Plastisol (veriler.md)
P.rho_p   = 1200;          % kg/m3
P.c_p     = 1350;          % J/(kg K)
P.k_p     = 0.14;          % W/(m K)
P.T_g     = 70 + 273.15;   % K, jelleşme başlangıcı
P.eta_ref = 3;             % Pa s
P.T_ref   = 23 + 273.15;   % K
P.E_a     = 40800;         % J/mol
P.gamma   = 0.032;         % N/m
P.eps     = 0.04;          % kür çekmesi
% Mandrel (316L, dolu)
P.rho_m = 7990;            % kg/m3
P.c_m   = 500;             % J/(kg K)
P.k_m   = 16.2;            % W/(m K)
P.R     = 4.0e-3;          % m, ID/2
P.L     = 0.400;           % m, kaplama boyu
% Proses
P.T_b    = 23 + 273.15;    % K, banyo
P.T_0    = 23 + 273.15;    % K, fırına giriş
P.T_amb  = 23 + 273.15;    % K, ortam
P.h_oven = 50;             % W/(m2 K)
P.h_amb  = 7.5;            % W/(m2 K)
P.t_tr   = 12;             % s, fırından banyoya taşıma
P.g      = 9.81;           % m/s2
% Model katsayıları
P.C_lld  = 0.94;
P.C_fib  = 1.34;
P.C_grav = 1.0;

% Hedef
s_hedef = 0.55e-3;         % m, kür sonrası iç katman

% İstasyon süreleri [s]
S.takt   = 240;
S.indeks = 12;
S.inis   = 2;              % indeks konumundan sıvı yüzeyine hızlı iniş
S.batir  = 10;             % 400 mm batırma
S.bekle  = 5;              % dipte bekleme (jel hesabındaki temas süresi)
S.damla  = 10;             % damlama beklemesi
S.kalkis = 2;              % sıvı yüzeyinden indeks konumuna

% İterasyon ayarları
U_alt = 0.1e-3;            % m/s, U1 arama alt sınırı
U_ust = 10e-3;             % m/s, U1 arama üst sınırı (servo eksen, varsayım)
tol_t = 1e-10;             % s, istasyon süresi toleransı
n_max = 60;                % U1 için en fazla iterasyon sayısı
T_ust = 250 + 273.15;      % K, T_m0 arama üst sınırı
tol_T = 0.01;              % K, T_m0 toleransı

% Sayısal ayarlar (programdaki "normal" kalite)
N.mandrel = 60;
N.bath    = 300;
N.steps   = 400;

%% 2) U1 iterasyonu: istasyon süresi = takt
t_sabit = S.indeks + S.inis + S.batir + S.bekle + S.damla + S.kalkis;
t_ist   = @(U) t_sabit + P.L./U;
f_U     = @(U) t_ist(U) - S.takt;

if f_U(U_ust) > 0
    error('U1 = %.2f mm/s ile bile istasyon süresi %.1f s > takt.', U_ust*1e3, t_ist(U_ust));
end
if f_U(U_alt) < 0
    error('U1 = %.2f mm/s ile bile istasyon süresi %.1f s < takt.', U_alt*1e3, t_ist(U_alt));
end

fprintf('--- U1 iterasyonu (ikiye bölme) ---\n');
fprintf('%4s %16s %16s %14s\n', 'k', 'U1 [mm/s]', 't_ist [s]', '|hata| [s]');
U_hist = nan(n_max, 1);              % iterasyon geçmişi (grafik için)
t_hist = nan(n_max, 1);
Ua = U_alt;  Ub = U_ust;
for k = 1:n_max
    Um = 0.5*(Ua + Ub);
    fm = f_U(Um);
    U_hist(k) = Um;
    t_hist(k) = t_ist(Um);
    fprintf('%4d %16.10f %16.10f %14.3e\n', k, Um*1e3, t_hist(k), abs(fm));
    if abs(fm) < tol_t
        break
    end
    if fm > 0          % istasyon uzun -> daha hızlı çek
        Ua = Um;
    else
        Ub = Um;
    end
end
n_U = k;
U_hist = U_hist(1:n_U);
t_hist = t_hist(1:n_U);
U1 = Um;
if abs(fm) >= tol_t
    fprintf('Not: %d iterasyonda tolerans (%.1e s) sağlanamadı, son hata %.3e s.\n', n_max, tol_t, abs(fm));
end

%% 3) Film (süzülme yok: h = h_0)
Rg  = 8.314462618;
eta = P.eta_ref*exp(P.E_a/Rg*(1/P.T_b - 1/P.T_ref));
[h0, formul, Ca] = film_kalinligi(U1, P.R, eta, P);    % R_s ilk tahmin: çıplak mandrel

s_film = (1 - P.eps)*h0;
if s_film >= s_hedef
    error(['Film tek başına hedefi aşıyor: (1 − ε)·h_0 = %.3f mm ≥ %.3f mm. ' ...
           'Bu takt ile hedef kalınlık tutturulamaz (jel gerekmiyor, film fazla).'], ...
          s_film*1e3, s_hedef*1e3);
end

%% 4) T_m0 iterasyonu: s_1 = s_hedef
f_T = @(T) s1_hesap(T, U1, eta, P, S, N) - s_hedef;
if f_T(T_ust) < 0
    error('T_m0 = %.0f °C ile bile hedef kalınlığa ulaşılamıyor.', T_ust - 273.15);
end

fprintf('\n--- T_m0 iterasyonu (ikiye bölme) ---\n');
fprintf('%4s %12s %14s %14s\n', 'k', 'T_m0 [°C]', 's_jel [mm]', 's_1 [mm]');
Ta = P.T_g;  Tb = T_ust;  k = 0;
while (Tb - Ta) > tol_T
    k  = k + 1;
    Tm = 0.5*(Ta + Tb);
    [s1m, sjm] = s1_hesap(Tm, U1, eta, P, S, N);
    fprintf('%4d %12.2f %14.4f %14.4f\n', k, Tm - 273.15, sjm*1e3, s1m*1e3);
    if s1m < s_hedef
        Ta = Tm;
    else
        Tb = Tm;
    end
end
T_m0 = 0.5*(Ta + Tb);
[s1, s_jel, h0, formul, Ca] = s1_hesap(T_m0, U1, eta, P, S, N);

%% 5) Ön ısıtma fırın sıcaklığı (D1 tersine)
t_pre  = S.takt - S.indeks;
tau    = P.rho_m*P.c_m*P.R/(2*P.h_oven);
tau_t  = P.rho_m*P.c_m*P.R/(2*P.h_amb);
Bi     = P.h_oven*P.R/(2*P.k_m);
T_exit = P.T_amb + (T_m0 - P.T_amb)*exp(P.t_tr/tau_t);
e      = exp(-t_pre/tau);
T_oven = (T_exit - P.T_0*e)/(1 - e);

%% 6) Sonuçlar
t_suz_ust = P.L/U1 + S.damla + S.kalkis + S.indeks;   % bilgi amaçlı (kalınlığa etkisi iptal)
t_suz_alt = S.damla + S.kalkis + S.indeks;

fprintf('\n============ 1. DALDIRMA – %g s TAKT (süzülme iptal) ============\n', S.takt);
fprintf('Çekme hızı U1                 : %.4f mm/s\n', U1*1e3);
fprintf('Çekme süresi L/U1             : %.1f s\n', P.L/U1);
fprintf('İstasyon süresi (indeks dahil): %.2f s\n', t_ist(U1));
fprintf('  indeks %g + iniş %g + batırma %g + bekleme %g + çekme %.1f + damla %g + kalkış %g\n', ...
        S.indeks, S.inis, S.batir, S.bekle, P.L/U1, S.damla, S.kalkis);
fprintf('Banyo viskozitesi eta_b       : %.2f Pa s\n', eta);
fprintf('Çekme anı film h_0            : %.3f mm  (%s, Ca = %.3f)\n', h0*1e3, formul, Ca);
fprintf('Banyoya giriş sıcaklığı T_m0  : %.1f °C\n', T_m0 - 273.15);
fprintf('Jel katmanı s_jel             : %.3f mm\n', s_jel*1e3);
fprintf('s_1 = (1 − ε)(s_jel + h_0)    : %.3f mm  (hedef %.3f mm)\n', s1*1e3, s_hedef*1e3);
fprintf('Fırın çıkışı sıcaklığı        : %.1f °C  (t_taşıma = %g s)\n', T_exit - 273.15, P.t_tr);
fprintf('Ön ısıtma fırını T_fırın      : %.1f °C  (t_ön = %g s, tau = %.0f s, Bi = %.3f)\n', ...
        T_oven - 273.15, t_pre, tau, Bi);
fprintf('Bekleme süresi (bilgi) üst / alt uç : %.1f / %.1f s  (süzülme iptal, kalınlığa etkisiz)\n', ...
        t_suz_ust, t_suz_alt);
if Bi >= 0.1
    fprintf('UYARI: Bi = %.3f ≥ 0,1, toplu kütle (D1) varsayımı geçersiz.\n', Bi);
end

%% 7) U1 iterasyon grafikleri
figure('Name', 'U1 iterasyonu');

subplot(1, 3, 1);
plot(1:n_U, U_hist*1e3, 'o-', 'LineWidth', 1.2); hold on;
yline(U1*1e3, '--r', sprintf('U1 = %.4f mm/s', U1*1e3));
xlabel('İterasyon k'); ylabel('U1 [mm/s]'); grid on;
title('U1 yakınsaması');

subplot(1, 3, 2);
semilogy(1:n_U, abs(t_hist - S.takt), 's-', 'LineWidth', 1.2); hold on;
yline(tol_t, '--r', 'tolerans');
xlabel('İterasyon k'); ylabel('|t_{ist} − takt| [s]'); grid on;
title('İstasyon süresi hatası');

subplot(1, 3, 3);
U_egri = linspace(max(U_alt, 0.5*U1), min(U_ust, 3*U1), 300);
plot(U_egri*1e3, t_ist(U_egri), 'LineWidth', 1.5); hold on;
yline(S.takt, '--k', sprintf('takt = %g s', S.takt));
gor = (U_hist >= U_egri(1)) & (U_hist <= U_egri(end));
plot(U_hist(gor)*1e3, t_hist(gor), 'o', 'MarkerSize', 5);
plot(U1*1e3, t_ist(U1), 'r*', 'MarkerSize', 12);
xlabel('U1 [mm/s]'); ylabel('t_{ist} [s]'); grid on;
legend('t_{ist}(U1)', 'takt', 'iterasyon noktaları', 'çözüm', 'Location', 'northeast');
title('İstasyon süresi – çekme hızı');


%% ===================== Yerel fonksiyonlar =====================

function [s1, s_jel, h0, formul, Ca] = s1_hesap(T_m0, U, eta, P, S, N)
% Verilen T_m0 ve U için kür sonrası iç katman (süzülme yok).
    s_jel = jel_kalinligi(T_m0, S.bekle, P, N);
    [h0, formul, Ca] = film_kalinligi(U, P.R + s_jel, eta, P);
    s1 = (1 - P.eps)*(s_jel + h0);
end


function [h0, formul, Ca] = film_kalinligi(U, R_s, eta, P)
% D7: çekme anındaki film kalınlığı (otomatik formül seçimi).
    l_c = sqrt(P.gamma/(P.rho_p*P.g));
    Ca  = eta*U/P.gamma;
    if R_s > l_c
        h_a = P.C_lld*(eta*U)^(2/3)/(P.gamma^(1/6)*sqrt(P.rho_p*P.g));
        h_c = P.C_grav*sqrt(eta*U/(P.rho_p*P.g));
        if h_a <= h_c
            h0 = h_a;  formul = 'D7a';
        else
            h0 = h_c;  formul = 'D7c';
        end
    else
        h0 = P.C_fib*R_s*Ca^(2/3);  formul = 'D7b';
    end
end


function s_gel = jel_kalinligi(T_m0, t_wait, P, N)
% D3: dolu mandrel + plastisol banyosu, radyal sonlu hacim, Crank–Nicolson
% (ilk 4 adım tam örtük), zaman adımları t_k = t·(k/n)^2. Jel cephesi: T ≥ T_g olan
% en dış nokta; jelleşme geri dönüşsüz.
    if T_m0 <= P.T_g
        s_gel = 0;
        return
    end
    alpha_p = P.k_p/(P.rho_p*P.c_p);
    R_far   = P.R + max(5*sqrt(alpha_p*t_wait), 3e-3);

    f_m   = linspace(0, P.R, N.mandrel + 1);
    f_b   = linspace(P.R, R_far, N.bath + 1);
    faces = [f_m, f_b(2:end)]';
    rc    = 0.5*(faces(1:end-1) + faces(2:end));
    n     = numel(rc);
    im    = N.mandrel;                          % son mandrel hücresi

    rho = [P.rho_m*ones(im,1); P.rho_p*ones(n-im,1)];
    cp  = [P.c_m*ones(im,1);   P.c_p*ones(n-im,1)];
    k   = [P.k_m*ones(im,1);   P.k_p*ones(n-im,1)];
    T   = [T_m0*ones(im,1);    P.T_b*ones(n-im,1)];

    C     = rho.*cp.*0.5.*(faces(2:end).^2 - faces(1:end-1).^2);
    fi    = faces(2:end-1);
    G     = fi./((fi - rc(1:end-1))./k(1:end-1) + (rc(2:end) - fi)./k(2:end));
    G_out = faces(end)*k(end)/(faces(end) - rc(end));

    d = zeros(n,1);
    d(1:end-1) = d(1:end-1) - G;
    d(2:end)   = d(2:end)   - G;
    d(end)     = d(end)     - G_out;
    A = sparse([1:n, 2:n, 1:n-1], [1:n, 1:n-1, 2:n], [d; G; G], n, n);
    b = zeros(n,1);  b(end) = G_out*P.T_b;
    Cd = spdiags(C, 0, n, n);

    t = t_wait*((0:N.steps)/N.steps).^2;
    rr = [P.R; rc(im+1:end)];
    wl = k(im)/(P.R - rc(im));
    wr = k(im+1)/(rc(im+1) - P.R);
    s_gel = 0;
    for j = 1:N.steps
        dt = t(j+1) - t(j);
        if j <= 4
            th = 1.0;
        else
            th = 0.5;
        end
        M   = Cd/dt - th*A;
        rhs = (C/dt).*T + (1 - th)*(A*T) + b;
        T   = M\rhs;

        % jel cephesi
        T_if = (wl*T(im) + wr*T(im+1))/(wl + wr);
        TT   = [T_if; T(im+1:end)];
        jj   = find(TT >= P.T_g, 1, 'last');
        if isempty(jj)
            s_raw = 0;
        elseif jj == numel(TT)
            s_raw = rr(end) - P.R;
        else
            T1 = TT(jj);  T2 = TT(jj+1);
            if T1 ~= T2
                fr = (T1 - P.T_g)/(T1 - T2);
            else
                fr = 0;
            end
            s_raw = rr(jj) + fr*(rr(jj+1) - rr(jj)) - P.R;
        end
        s_gel = max(s_gel, s_raw);
    end
end
